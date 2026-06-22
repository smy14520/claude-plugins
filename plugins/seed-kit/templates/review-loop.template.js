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
//   ① assert 客观锚（没绿直接 impl，不浪费语义 review）
//   ② code-review（审代码主线）+ judge（审产物）并行
//   ③ propose-kill：每条 finding 派 3 validator 投票（≥2 refute 才杀，学 /deep-research）
//   ④ 收敛：survived blocking 清空 → break
//   ⑤ circuit breaker：issues_hash 重复/无进展/max rounds → 熔断 escalate
//   ⑥ impl 修 survived blocking

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
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdict: { type: 'string', enum: ['valid', 'invalid', 'ambiguous'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    counter_evidence: { type: 'string' },
  },
  required: ['verdict', 'counter_evidence'],
}

// 简单 hash：检测"换汤不换药"（同一批 blocking finding 反复出现）
const hashClaims = (arr) => {
  const s = JSON.stringify((arr || []).map((f) => f.claim).sort())
  let h = 0; for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0
  return h
}
const trim = (s, n) => (typeof s === 'string' ? s.slice(0, n) : '')

phase('Audit')
let round = 0, prevHash = null, stall = 0, escalated = false
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

  const findings = [...(codeRes.findings || []), ...(judgeRes.findings || [])]

  // ③ propose-kill：每条 finding 派 3 个 validator 投票（学 /deep-research 对抗验证）
  //    ≥ REFUTATIONS_REQUIRED 个 refute 才杀；null(弃权) 不当 refute 也不当 support，
  //    survive 要求足够多真裁决（防"全弃权→refute=0→假 survive"）
  const VOTES_PER_FINDING = 3, REFUTATIONS_REQUIRED = 2
  const voted = (await parallel(findings.map((f) => () =>
    parallel(Array.from({ length: VOTES_PER_FINDING }, (_, v) => () =>
      agent(
        `对抗证伪 finding（voter ${v + 1}/${VOTES_PER_FINDING}）。Be SKEPTICAL，尽力 REFUTE——≥${REFUTATIONS_REQUIRED}/${VOTES_PER_FINDING} refute 才杀。\n` +
        `claim: ${f.claim}\nevidence: ${f.evidence}\nseverity: ${f.severity}\n` +
        `checklist：(1) claim 是否真被 evidence 支持；(2) 读 ${REPO} 相关代码找反证；(3) severity 是否夸大；(4) 是否过度报告（把 AC 没要求的当问题）。\n` +
        `verdict=invalid（refute）必须附 file:line 反证；verdict=valid（成立）说明为何站得住。Default to invalid if uncertain（bias toward refute）。`,
        { agentType: 'seed-kit:seed-validator', schema: VERDICT_SCHEMA, label: `vote${v}:${f.id}:r${round}`, phase: 'Audit' }
      )
    )).then((vs) => {
      const valid = vs.filter(Boolean)  // null = 弃权（agent error/skip）
      const refuted = valid.filter((x) => x.verdict === 'invalid').length
      const abstained = VOTES_PER_FINDING - valid.length
      const survives = valid.length >= REFUTATIONS_REQUIRED && refuted < REFUTATIONS_REQUIRED
      log(`"${f.claim.slice(0, 40)}…": ${valid.length - refuted}-${refuted}${abstained > 0 ? ` (${abstained} 弃权)` : ''} ${survives ? '✓' : '✗'}`)
      return { ...f, refutedVotes: refuted, abstained, survives }
    })
  ))).filter(Boolean)
  const survived = voted.filter((v) => v.survives)
  const killed = voted.filter((v) => !v.survives)
  const blocking = survived.filter((f) => f.severity === 'blocking')

  rounds.push({
    round, code_findings: (codeRes.findings || []).length, judge_findings: (judgeRes.findings || []).length,
    survived: survived.length, killed: killed.map((f) => f.claim), blocking: blocking.map((f) => f.claim),
  })

  // ④ 收敛
  if (blocking.length === 0) { log(`CONVERGED at round ${round}`); break }

  // ⑤ circuit breaker：同一批 blocking 连续 2 轮相同 = impl 没真修（换汤不换药）→ 熔断
  //    语义：本轮 blocking 的 hash 与上一轮相同 → stall=1 → 立即熔断（不等到第 3 轮）
  const h = hashClaims(blocking)
  stall = h === prevHash ? stall + 1 : 0
  prevHash = h
  if (stall >= 1) { escalated = true; log(`CIRCUIT BREAKER: blocking 连续 ${stall + 1} 轮相同，impl 未真修，escalate`); break }

  // ⑥ impl 修 survived blocking（改完必须自跑测试验 PASS_TO_PASS 并报回——下一轮 assert 会客观复核）
  await agent(`修这些 survived blocking finding。改完必须跑测试验证既有用例仍绿（PASS_TO_PASS），把测试结果报回：\n${blocking.map((f) => '- ' + f.claim).join('\n')}`,
    { agentType: 'seed-kit:seed-impl', label: `impl:r${round}`, phase: 'Audit' })
}

// —— 精简 return（防 structuredClone 崩）——
return {
  task: TASK, slice: SLICE, rounds: round,
  converged: !escalated && rounds.length > 0 && (rounds[rounds.length - 1].blocking || []).length === 0,
  escalated,
  verdict: escalated ? 'ESCALATED — circuit breaker 触发，未决项交人'
    : (rounds[rounds.length - 1] && (rounds[rounds.length - 1].blocking || []).length === 0
      ? `CONVERGED — ${round} 轮，可推进 done`
      : `NOT CONVERGED — ${MAX_ROUNDS} 轮仍有 blocking`),
  trace: rounds,
}
