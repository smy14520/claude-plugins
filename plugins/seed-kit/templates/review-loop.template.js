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
//   ① assert 客观锚（null→impl 自查使可达；没绿→impl 修；都不浪费语义 review）
//   ② code-review（审代码主线）+ judge（审产物）并行；一路 null=盲审
//   ③ propose-kill：JURY 个 validator 各自批量证伪全部 finding（默认 1，不随 finding 数膨胀）
//   ④ 收敛：两路 reviewer 都非 null 且 survived blocking 清空 → converged
//   ⑤ 熔断：盲审 / blocking 连续相同 / assert 连续未绿 / max rounds → escalate，绝不推 done
//   ⑥ impl 修 survived blocking
// 终态由显式 terminalReason 驱动 verdict，不从 rounds 反推（防 assert 未绿却假报 converged）

export const meta = {
  name: 'seed-review-loop',
  description: 'seed-kit review loop：代码审计(主线)+产物judge+客观assert+propose-kill，loop 到收敛或熔断',
  phases: [
    { title: 'Audit', detail: '每轮：assert 客观锚 → code-review + judge → propose-kill → 收敛/circuit breaker → impl' },
  ],
}

// —— args 修法：当前 runtime 把 args 对象序列化成字符串注入 ——
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const TASK = A.task                    // 必填：任务目录名，如 family-ledger
const SLICE = A.slice || null          // 可选：单 slice id（如 S-005）；null = 审整个任务
const REPO = A.repo || '.'             // 项目根（默认 cwd）
const MAX_ROUNDS = A.max_rounds || 3   // 熔断兜底

// —— schema（与 S-008 验证版一致）——
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

// 简单 hash：检测"换汤不换药"（同一批 blocking finding 反复出现）
const hashClaims = (arr) => {
  const s = JSON.stringify((arr || []).map((f) => f.claim).sort())
  let h = 0; for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0
  return h
}
const trim = (s, n) => (typeof s === 'string' ? s.slice(0, n) : '')

phase('Audit')
let round = 0, prevHash = null, stall = 0, escalated = false, terminalReason = null
const rounds = []

while (round < MAX_ROUNDS) {
  round++
  log(`round ${round}/${MAX_ROUNDS}`)

  // ① assert 客观锚：assert 没绿 → 直接 impl 修客观问题，不进语义 review
  const assertRes = await agent(
    `跑 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的 [assert] 义务，用 seed run-check 真实落 evidence。` +
    `项目根 ${REPO}。all_passed = 全部 exit 0。失败把 failures 列出。`,
    { agentType: 'seed-kit:seed-assert', schema: ASSERT_SCHEMA, label: `assert:r${round}`, phase: 'Audit' }
  )
  // assert 不可达（agent 返回 null/形状错）：按未通过处理，派 impl 自查使可达——不复用 escalated
  // （那是 impl 停滞的 circuit breaker，合流会把 runtime 失败误诊为“impl 没真修”）
  const assertOk = assertRes && typeof assertRes.all_passed === 'boolean'
  if (!assertOk) {
    await agent(`assert 客观锚不可达（seed-assert 未返回有效 all_passed）。自查 [assert] 义务能否真实执行（seed run-check 路径/命令/环境可达），修复使其能跑出真实结果。改完跑测试验 PASS_TO_PASS 报回。`,
      { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
    rounds.push({ round, stage: 'assert-unavailable' })
    continue
  }
  if (!assertRes.all_passed) {
    await agent(`修这些 assert 失败。改完必须跑测试验证既有用例仍绿（PASS_TO_PASS），把结果报回：\n${assertRes.failures}`,
      { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
    rounds.push({ round, stage: 'assert-failed' })
    continue
  }

  // ② code-review（审代码主线）+ judge（审产物）并行
  const [codeRes, judgeRes] = await parallel([
    () => agent(
      `审 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的【代码】。先读 ${REPO}/.arbor/tasks/${TASK}/slices/${SLICE || '所有'}.md 拿 AC 与交付面，` +
      `再在 ${REPO} 下找到对应实现代码（Glob/Grep），逐 AC 审：兑现？偷懒签名？隐患？出 finding（file:line 证据）。不审产物。`,
      { agentType: 'seed-kit:seed-review', schema: FINDINGS_SCHEMA, label: `review:code:r${round}`, phase: 'Audit' }
    ),
    () => agent(
      `审 ${TASK}${SLICE ? ' / ' + SLICE : ''} 的【产物】。读 slice 拿 [judge] 义务与 rubric，在 ${REPO} 下找对应产物（前端页面/截图/输出）。` +
      `产物缺失/不可达 = blocking missing-deliverable。按 rubric 评，出 finding。`,
      { agentType: 'seed-kit:seed-judge', schema: FINDINGS_SCHEMA, label: `judge:r${round}`, phase: 'Audit' }
    ),
  ])

  const codeFindings = (codeRes && codeRes.findings) || []
  const judgeFindings = (judgeRes && judgeRes.findings) || []
  const findings = [...codeFindings, ...judgeFindings]
  const blindSpot = !codeRes || !judgeRes  // 一路 reviewer 返回 null = 盲审，不能当“无 finding=通过”

  // ③ propose-kill：JURY 个 validator 各自一次批量证伪全部 finding
  //    成本固定不随 finding 数膨胀（旧版 = 3×N 扇出，是一轮 agent 数的主体）；JURY=A.jury 默认 1，设 2 加对抗冗余
  //    kill 规则：≥1 invalid 且无人 valid → 杀（一个 valid 即保命，保守不误杀真问题；全员黑掉=不杀=安全不收敛）
  const JURY = A.jury || 1
  const juryOut = findings.length === 0 ? [] : (await parallel(Array.from({ length: JURY }, (_, j) => () =>
    agent(
      `对抗证伪本轮全部 finding（reviewer ${j + 1}/${JURY}）。逐条尽力 REFUTE，bias toward invalid。\n` +
      `逐条按 id 裁决（一个都不能漏），输出 verdict：invalid（refute，须附 file:line/命令反证）/ valid（成立，说明为何站得住）/ ambiguous。` +
      `checklist：(1) claim 是否真被 evidence 支持；(2) 读 ${REPO} 相关代码找反证；(3) severity 是否夸大；(4) 是否过度报告（把 AC 没要求的当问题）。\n` +
      `Default invalid if uncertain；但口头"我觉得没问题"不算反证——给不出反证就 valid。\n\n` +
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
  const blocking = survived.filter((f) => f.severity === 'blocking')
  log(`propose-kill r${round}: ${survived.length} survived / ${killed.length} killed${blocking.length ? ` (${blocking.length} blocking)` : ''}`)

  rounds.push({
    round, code_findings: codeFindings.length, judge_findings: judgeFindings.length,
    survived: survived.length, killed: killed.map((f) => f.claim), blocking: blocking.map((f) => f.claim),
    ...(blindSpot ? { blind_spot: true } : {}),
  })

  // ④ 收敛：要求两路 reviewer 都非 null 且无 survived blocking（防“没审=通过”假收敛）
  if (!blindSpot && blocking.length === 0) { terminalReason = 'converged'; log(`CONVERGED at round ${round}`); break }
  //    盲审（一路 reviewer 返回 null）：即使 blocking 空也不能判通过，escalate 交人
  if (blindSpot) { escalated = true; terminalReason = 'reviewer-blind'; log(`CIRCUIT BREAKER: reviewer 盲审（${!codeRes ? 'code' : ''}${!codeRes && !judgeRes ? '+' : ''}${!judgeRes ? 'judge' : ''} 返回 null），escalate`); break }

  // ⑤ circuit breaker：同一批 blocking 连续 2 轮相同 = impl 没真修（换汤不换药）→ 熔断
  //    语义：本轮 blocking 的 hash 与上一轮相同 → stall=1 → 立即熔断（不等到第 3 轮）
  const h = hashClaims(blocking)
  stall = h === prevHash ? stall + 1 : 0
  prevHash = h
  if (stall >= 1) { escalated = true; terminalReason = 'circuit-breaker'; log(`CIRCUIT BREAKER: blocking 连续 ${stall + 1} 轮相同，impl 未真修，escalate`); break }

  // ⑥ impl 修 survived blocking（改完必须自跑测试验 PASS_TO_PASS 并报回——下一轮 assert 会客观复核）
  await agent(`修这些 survived blocking finding。改完必须跑测试验证既有用例仍绿（PASS_TO_PASS），把测试结果报回：\n${blocking.map((f) => '- ' + f.claim).join('\n')}`,
    { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
}

// while 自然退出（耗尽 MAX_ROUNDS）→ 按末轮 stage 推断终态；assert 连续未绿绝不判 converged
if (!terminalReason) {
  const last = rounds[rounds.length - 1]
  terminalReason = (last && last.stage === 'assert-failed') ? 'assert-stalled'
    : (last && last.stage === 'assert-unavailable') ? 'assert-unavailable'
    : 'rounds-exhausted'
}

// —— 精简 return（防 structuredClone 崩）——
return {
  task: TASK, slice: SLICE, rounds: round,
  terminal_reason: terminalReason,
  converged: terminalReason === 'converged',
  escalated,
  verdict: terminalReason === 'converged' ? `CONVERGED — ${round} 轮，可推进 done`
    : terminalReason === 'assert-stalled' ? `ESCALATED — 客观锚连续未绿（assert-stalled），绝不推 done`
    : terminalReason === 'assert-unavailable' ? `ESCALATED — assert 客观锚不可达，交人`
    : terminalReason === 'reviewer-blind' ? `ESCALATED — reviewer 盲审（code/judge 返回 null），交人`
    : terminalReason === 'circuit-breaker' ? `ESCALATED — circuit breaker 触发，未决项交人`
    : `NOT CONVERGED — ${MAX_ROUNDS} 轮仍有 blocking`,
  trace: rounds,
}
