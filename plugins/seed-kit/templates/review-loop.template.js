// seed-kit review-loop 模板（参考脚本，不是被插件加载的 workflow 工件）
//
// 背景：Claude Code 插件不能分发 workflow 工件（workflows/ 非插件标准目录）。
// 所以 review SKILL 指导 Claude 读本模板 → 按 task/slice 填 args → 用 Workflow 工具跑。
// 本模板是"编排蓝图"，固化了验证过的控制流与所有已知坑的修法。
//
// 已固化修法：
// - args 在当前 runtime 被 stringify 注入 → 开头 JSON.parse 还原（别用默认值验证 args）。
// - return 精简（只 claim 级 + 截断 evidence）→ 防 structuredClone 崩。
// - agentType 指向插件 agent（seed-kit:seed-*）→ 角色硬分离、生成者≠验证者。
//
// 控制流（每轮做满）：
//   ① 客观锚：跑项目声明的测试+质量命令（lint/typecheck/build），不绿→impl 修
//   ② code-review（审代码）+ judge（审产物）并行；一路 null=盲审
//   ③ propose-kill：JURY 个 validator 各自批量证伪全部 finding（默认 1）
//   ④ 收敛：两路 reviewer 都非 null 且 survived blocking 清空 → converged
//   ⑤ 熔断：盲审 / blocking 连续相同 / 客观锚连续未绿 / max rounds → escalate，绝不推 done
//   ⑥ impl 修 survived blocking
// 终态由显式 terminalReason 驱动 verdict，不从 rounds 反推

export const meta = {
  name: 'seed-review-loop',
  description: 'seed-kit review loop：代码审计(主线)+产物judge+客观锚+propose-kill，loop 到收敛或熔断',
  phases: [
    { title: 'Audit', detail: '每轮：客观锚 → code-review + judge → propose-kill → 收敛/circuit breaker → impl' },
  ],
}

// —— args 修法：当前 runtime 把 args 对象序列化成字符串注入 ——
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const TASK = A.task                    // 必填：任务目录名
const SLICE = A.slice || null          // 可选：单 slice id（如 S-005）；null = 审整个任务
const REPO = A.repo || '.'             // 项目根（默认 cwd）
const MAX_ROUNDS = A.max_rounds || 3   // 熔断兜底

// —— schema ——
const FINDINGS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    summary: { type: 'string' },
    findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        id: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'major', 'minor', 'ok'] },
        category: { type: 'string', enum: ['correctness', 'lazy-signature', 'hazard', 'missing-deliverable', 'experience'] },
        claim: { type: 'string' }, evidence: { type: 'string' },
      }, required: ['id', 'severity', 'category', 'claim', 'evidence'],
    } },
  }, required: ['summary', 'findings'],
}
const ASSERT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { all_passed: { type: 'boolean' }, failures: { type: 'string' }, summary: { type: 'string' } },
  required: ['all_passed', 'summary'],
}
const BATCH_VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { verdicts: { type: 'array', items: {
    type: 'object', additionalProperties: false,
    properties: {
      id: { type: 'string' },
      verdict: { type: 'string', enum: ['valid', 'invalid', 'ambiguous'] },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      counter_evidence: { type: 'string' },
    }, required: ['id', 'verdict', 'counter_evidence'],
  } } },
  required: ['verdicts'],
}

const hashClaims = (arr) => {
  const s = JSON.stringify((arr || []).map((f) => f.claim).sort())
  let h = 0; for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0
  return h
}

phase('Audit')
let round = 0, prevHash = null, stall = 0, escalated = false, terminalReason = null
const rounds = []

while (round < MAX_ROUNDS) {
  round++
  log(`round ${round}/${MAX_ROUNDS}`)

  // ① 客观锚：跑项目声明的测试+质量命令。不绿 → impl 修，不浪费语义 review
  const assertRes = await agent(
    `跑 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的客观锚。项目根 ${REPO}。\n` +
    `读项目配置文件（package.json / Makefile / pyproject.toml / Cargo.toml），` +
    `找到项目声明的测试命令 + 质量命令（lint / typecheck / build 等）。` +
    `逐条执行。exit 0 即 passed。全部通过 → all_passed=true。` +
    `有失败的 → all_passed=false + failures 列出失败命令和输出。`,
    { agentType: 'seed-kit:seed-assert', schema: ASSERT_SCHEMA, label: `assert:r${round}`, phase: 'Audit' }
  )
  const assertOk = assertRes && typeof assertRes.all_passed === 'boolean'
  if (!assertOk) {
    await agent(`客观锚不可达（seed-assert 未返回有效 all_passed）。自查项目测试/质量命令能否真实执行，修复使其能跑出真实结果。改完跑测试验 PASS_TO_PASS 报回。`,
      { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
    rounds.push({ round, stage: 'assert-unavailable' })
    continue
  }
  if (!assertRes.all_passed) {
    await agent(`修这些测试/质量命令失败。改完必须跑测试验证既有用例仍绿（PASS_TO_PASS），把结果报回：\n${assertRes.failures}`,
      { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
    rounds.push({ round, stage: 'assert-failed' })
    continue
  }

  // ② code-review（审代码主线）+ judge（审产物）并行
  const [codeRes, judgeRes] = await parallel([
    () => agent(
      `审 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的【代码】。\n` +
      `**先读** ${REPO}/CLAUDE.md、${REPO}/DESIGN.md、${REPO}/.claude/rules/（项目质量标准，有就全读，没有跳过）。\n` +
      `再读 ${REPO}/.arbor/tasks/${TASK}/prd.md 的 \`## Goal\`（任务概述 + 方向描述）和 \`### S-NNN\` 的 \`* [ ]\` 条目。\n` +
      `再在 ${REPO} 下找到对应实现代码（Glob/Grep）。\n\n` +
      `审五层（每层是动作，必须执行）：\n` +
      `① **兑现**：逐验收条目打开实现文件和测试文件，标注每条条目中行为在代码里的实现位置(file:line)和测试覆盖。没有实现或没有测试的条目 → finding。\n` +
      `② **偷懒签名**：读测试文件，验断言是否真触及条目声称的可观测行为（而非只测代理指标如 class 存在就过）。同样查：吞异常 / 抄实现的假测试 / 悄悄收窄 scope / 边界与失败路径没真覆盖。\n` +
      `③ **隐患**：读 diff 中错误处理、外部数据入口、状态变更路径。外部 I/O 无错误处理 / 外部数据无输入校验 / 权限 / 数据一致 / 并发 / 安全问题 → finding(file:line)。\n` +
      `④ **工程卫生**：跑项目 lint/type-check/build → 查 debug log / 死代码 / 抑制性注解 → New function → unit test? Bug fix → regression test? Changed behavior → existing tests updated?\n` +
      `⑤ **方向对账**：按 PRD 的 Goal + DESIGN.md ——代码是否支持 PRD 中描述的方向？有什么明明可以做但没做的？→ finding(severity=major, category=experience)。\n\n` +
      `出 finding（file:line 证据）。没问题的方面在 summary 说明。不审产物。`,
      { agentType: 'seed-kit:seed-review', schema: FINDINGS_SCHEMA, label: `review:code:r${round}`, phase: 'Audit' }
    ),
    () => agent(
      `审 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的【产物】。\n` +
      `**先读** ${REPO}/.arbor/tasks/${TASK}/prd.md 的 \`## Goal\`（任务概述 + 方向描述）和 \`### S-NNN\` 的 \`* [ ]\` 条目。\n` +
      `再读 ${REPO}/DESIGN.md（如存在）。\n\n` +
      `审真实产物（可感知输出/运行实例/生成文件——不是代码）：\n` +
      `- 产物是否兑现了 PRD 中描述的方向？\n` +
      `- 对照 DESIGN.md（如有）：客观骨架（配色/字体/布局）是否对齐？\n` +
      `- **missed-opportunity**：给定 PRD 中描述的方向，什么是明明可以做但没做的？作为 experience 级 finding（不 blocking）给实现者改进方向。\n` +
      `- 产物缺失/不可达 → blocking missing-deliverable。\n\n` +
      `出 finding。无可感面时 → 返回空 findings + summary 说明原因。`,
      { agentType: 'seed-kit:seed-judge', schema: FINDINGS_SCHEMA, label: `judge:r${round}`, phase: 'Audit' }
    ),
  ])

  const codeFindings = (codeRes && codeRes.findings) || []
  const judgeFindings = (judgeRes && judgeRes.findings) || []
  const findings = [...codeFindings, ...judgeFindings]
  const blindSpot = !codeRes || !judgeRes

  // ③ propose-kill：JURY 个 validator 各自一次批量证伪全部 finding
  const JURY = A.jury || 1
  const juryOut = findings.length === 0 ? [] : (await parallel(Array.from({ length: JURY }, (_, j) => () =>
    agent(
      `对抗证伪本轮全部 finding（reviewer ${j + 1}/${JURY}）。逐条尽力 REFUTE，bias toward invalid。\n` +
      `逐条按 id 裁决（一个都不能漏），输出 verdict：invalid（refute，须附 file:line/命令反证）/ valid（成立，说明为何站得住）/ ambiguous。` +
      `checklist：(1) claim 是否真被 evidence 支持；(2) 读 ${REPO} 相关代码找反证；(3) severity 是否夸大；(4) 是否过度报告（把验收条目没要求的当问题）。\n` +
      `uncertain → valid（须给出具体反证 file:line/命令才能判 invalid；口头"我觉得没问题"不算反证）。severity 为 ok 的纯确认性 finding 默认 valid，不得以"过度报告"判 invalid——过度报告判定只适用于 blocking/major/minor。\n\n` +
      `findings:\n${findings.map((f) => `- [${f.id}] (${f.severity}/${f.category}) ${f.claim}\n  evidence: ${f.evidence}`).join('\n')}`,
      { agentType: 'seed-kit:seed-validator', schema: BATCH_VERDICT_SCHEMA, label: `validate:r${round}:${j + 1}`, phase: 'Audit' }
    )
  ))).filter(Boolean)

  const tally = {}
  for (const out of juryOut) {
    for (const it of (out.verdicts || [])) {
      const t = (tally[it.id] = tally[it.id] || { invalid: 0, valid: 0 })
      if (it.verdict === 'invalid') t.invalid++; else if (it.verdict === 'valid') t.valid++
    }
  }
  const voted = findings.map((f) => {
    const t = tally[f.id] || { invalid: 0, valid: 0 }
    const killed = t.invalid > 0 && t.valid === 0
    return { ...f, refutedVotes: t.invalid, validVotes: t.valid, survives: !killed }
  })
  const survived = voted.filter((v) => v.survives)
  const killed = voted.filter((v) => !v.survives)
  // missing-deliverable（测试/交付物缺失）一律算 blocking
  const blocking = survived.filter((f) => f.severity === 'blocking' || f.category === 'missing-deliverable')
  log(`propose-kill r${round}: ${survived.length} survived / ${killed.length} killed${blocking.length ? ` (${blocking.length} blocking)` : ''}`)

  rounds.push({
    round, code_findings: codeFindings.length, judge_findings: judgeFindings.length,
    survived: survived.length, killed: killed.map((f) => f.claim), blocking: blocking.map((f) => f.claim),
    ...(blindSpot ? { blind_spot: true } : {}),
  })

  // ④ 收敛：两路 reviewer 都非 null 且无 survived blocking
  if (!blindSpot && blocking.length === 0) { terminalReason = 'converged'; log(`CONVERGED at round ${round}`); break }
  // 盲审 → escalate
  if (blindSpot) { escalated = true; terminalReason = 'reviewer-blind'; log(`CIRCUIT BREAKER: reviewer 盲审（${!codeRes ? 'code' : ''}${!codeRes && !judgeRes ? '+' : ''}${!judgeRes ? 'judge' : ''} 返回 null），escalate`); break }

  // ⑤ circuit breaker：同一批 blocking 连续相同 → 熔断
  const h = hashClaims(blocking)
  stall = h === prevHash ? stall + 1 : 0
  prevHash = h
  if (stall >= 1) { escalated = true; terminalReason = 'circuit-breaker'; log(`CIRCUIT BREAKER: blocking 连续 ${stall + 1} 轮相同，impl 未真修，escalate`); break }

  // ⑥ impl 修 survived blocking
  await agent(`修这些 survived blocking finding。改完必须跑测试验证既有用例仍绿（PASS_TO_PASS），把测试结果报回：\n${blocking.map((f) => '- ' + f.claim).join('\n')}`,
    { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
}

// while 自然退出（耗尽 MAX_ROUNDS）
if (!terminalReason) {
  const last = rounds[rounds.length - 1]
  terminalReason = (last && last.stage === 'assert-failed') ? 'assert-stalled'
    : (last && last.stage === 'assert-unavailable') ? 'assert-unavailable'
    : 'rounds-exhausted'
}

return {
  task: TASK, slice: SLICE, rounds: round,
  terminal_reason: terminalReason,
  converged: terminalReason === 'converged',
  escalated,
  verdict: terminalReason === 'converged' ? `CONVERGED — ${round} 轮，可推进 done`
    : terminalReason === 'assert-stalled' ? `ESCALATED — 客观锚连续未绿（assert-stalled），绝不推 done`
    : terminalReason === 'assert-unavailable' ? `ESCALATED — 客观锚不可达，交人`
    : terminalReason === 'reviewer-blind' ? `ESCALATED — reviewer 盲审（code/judge 返回 null），交人`
    : terminalReason === 'circuit-breaker' ? `ESCALATED — circuit breaker 触发，未决项交人`
    : `NOT CONVERGED — ${MAX_ROUNDS} 轮仍有 blocking`,
  trace: rounds,
}
