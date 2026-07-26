# 优秀 AI 编程工作流扫描(2025-2026)

> 2026-07-26。逐个拆解业界高水平工作流的核心机制,标注 seed-kit 可吸收点。
> 判据沿用 [`STRONG_MODEL_RESEARCH.md`](STRONG_MODEL_RESEARCH.md):只吸收"提供模型无法自行推断的信息"或"激励对抗"类机制;能力补偿类一律不进。

## 逐家机制拆解

### Compound Engineering(Every / Kieran Klaassen)

Plan → Work → Review → **Compound** 四步循环;80% 时间在 plan+review。核心是第四步:每次 review 的教训被提取、打标签(YAML frontmatter)、写回 CLAUDE.md / docs/solutions,下一轮 brainstorm/plan 把它当 grounding 读入。`/ce-compound` 用 6 个并行 subagent 做提取(context analyzer / solution extractor / prevention strategist / …)。关键自检:"**这个教训下次系统能自动抓住吗?**"——教训的终态不是文档,是测试/规则。同时警告:"10 条你自己的具体规则胜过 100 条通用规则;剪枝和生长一样重要"。

**→ seed-kit**:这正是 seed-kit 缺的第四步。review-loop 终态目前只落 marker;P2 wiki 供给侧提案(从 finding/gate-attempts 提取候选草稿,人批准)就是 compound 步的机制化,现在有了生产级先例。更强形态:教训升格阶梯——prose(wiki)→ 项目规则(.claude/rules)→ 可执行(探针/测试/hook)。

### Beads(Steve Yegge)

给 agent 的图状 issue tracker:markdown 计划是"write-only memory",结构化任务图(`bd ready --json`)才能查询。四类依赖边,其中 **`discovered-from`** 最关键——实现途中发现的工作被结构化记录、永不丢失。"kill agent after each issue" 模式:每个 issue 一个干净 session,靠 `bd ready` 接续。教训:"agent 对约定的遵守随 context 增长衰减——hook 强制比 prompt 指示可靠"。

**→ seed-kit**:PRD checkbox + `seed status --json` 已是迷你版任务图,但**没有工作发现通道**——slice agent 途中发现的工作只进内存 handoff(会丢)。候选机制:`seed discover <task> "<描述>" [--from S-NNN]` 落盘到 task 目录,`status`/`next-action` 展示,收口时人裁决(入 PRD / 弃)。纯确定性 helper,符合教义。

### Amp(Sourcegraph)——活的脚手架贬值记录

Chronicle 时间线本身就是证据:2026-01 **删掉 TODO 功能**;2026-02 杀编辑器扩展;早期专门化 subagent 全部失败("模型不调用它们"),Sonnet 4 后通用 subagent 才起飞——**编排价值依赖模型代际,须随代际重估**。存留的机制:subagent 当"context 乘法器"(错误修复派新鲜 context,主 agent 只花派发的 token);**Oracle 模式**(更强/异构模型做评审,显式调用不自动);Handoff 替代 compaction("用户会察觉 agent 变笨了——手动控制优于自动截断")。

**→ seed-kit**:验证侧派生(review 家族独立 context)已对齐;Oracle 提示一个低成本选项——review-loop 的 judge/validator 支持异模型配置。TODO 之死佐证 seed-kit 不做第二套任务层的决定。

### Ralph 生态(Geoffrey Huntley,2026 演化)

本质不是"永远跑",是"**把工作切成独立 context window + 状态彻底外置**"(fix_plan.md/specs/git 在盘上,模型可抛弃)。对 Claude Code `/goal` 的社区批评极有价值:其完成 oracle 只读 transcript、**不能执行任何命令**——"退回到信任工作模型的自我汇报,恰是外部 oracle 本该消除的东西"。Ralph 操作清单:完成条件必须是机器可查谓词;显式迭代上限;**完成 oracle 必须是 agent 不可写的**;每轮 commit;context 拓扑要主动选。

**→ seed-kit**:`seed done` 真实执行命令,正是 /goal 缺的那种 oracle——设计被反向验证。"oracle 不可被 agent 写"直接支持 P1 评分链路防篡改提案(hook 拦 done-logs/gate-attempts 直写)。

### Anthropic 大规模迁移方法论(2026-07)

"**你不修代码,你修产出代码的循环**"。机制:(1) **rulebook 上移**——reviewer 反复抓到同类错误时,不逐文件修,往 rulebook 加一句话然后重生成,"代码从不被逐处 hand-patch";(2) **判官先行且必须校验**——judge 对原代码必须 pass、对故意破坏的代码必须 fail,"抓不住破坏的 judge 不是 judge";(3) 机械可续队列——"done = 文件在盘上",队列每次从盘上重建,天然可恢复;(4) 双对抗 reviewer 独立 context,分歧交第三方;(5) 同类失败跨多测试重复 → 修上游规则并只重生成该规则触及的文件。

**→ seed-kit**:(1) 映射 review-loop:同 category finding 重复出现 ≥N 次 → 提议沉淀为项目规则(.claude/rules,人批准),不只逐处修——compound 步的另一半;(2) judge 校验:evals-v2 已有 check-red,但**工作流内**的 judge/rubric 无自检——review-loop 可加"红样自检"轻量步;(3) 队列哲学与 checkbox 教义同构,互证。

### Anthropic verification loops(2026-07-22)

把手工检查编码为 skill,四级递进:standalone(手动调)→ embedded(产出型 skill 自带)→ **chained**(skill 链:/code-review → /simplify → /verify → /design,"习惯变成契约")→ PR 级(团队基建,不依赖作者自觉)。"信号:当你每次改动后都手动跑同一个检查,它就该升级了。"

**→ seed-kit**:review-loop 已是 chained 形态;这个"升级阶梯"可作为项目侧指导写进 verification.md——项目重复手检的东西应沉淀为质量命令(进 gate)或 review 维度。

### TDD Guard(nizos)

PreToolUse hook 拦 Write/Edit,用验证模型判 TDD 违规(无失败测试就实现/过度实现)。作者的三条教训:(1) hook 强制 > prompt 提醒(与 Beads 教训一致);(2) **机械合规 ≠ 质量**——强制 TDD 后代码仍然耦合重复设计差,"TDD 的价值来自心智不是规则遵守"——直接印证 seed-kit "gate 守硬事实、好坏走 review"的分层;(3) post-action hook 弱、会被拖延 → 把问题存下来在**下一次 pre-action 强制解决**(延迟强制模式,与 gate-attempts 思路同构)。

### Devin(Cognition)——知识层三件套

Skills(repo 内 SKILL.md,可执行程序性知识,**Devin 学到新东西后自动建议创建/更新 skill,一键 Create PR**)/ Knowledge(trigger description 驱动的按需检索,"相关时取,不一次全灌")/ Playbooks(org 级 prompt 模板,Procedure/Specifications/Advice/Forbidden Actions)。

**→ seed-kit**:auto-suggest + Create PR 是 wiki 供给侧的生产实现;trigger 检索即 wiki collect 的方向;分层(repo 程序性 / org 检索性 / 模板)可参考。

### OpenHands——path-triggered rules

四种触发:always(repo)/ keyword / task / **path**——agent 碰到匹配 glob 的文件时,规则**确定性注入到 tool result**,零基线成本、每会话去重、模型不可主动调用。这是"消费侧确定性窄注入"的干净实现(Claude Code rules 同构)。

**→ seed-kit**:wiki 消费侧改造(P2)的参照——wiki 条目声明 trigger(关键词或路径),编排点由 helper 机器注入,不靠模型记得查。

### Aider architect/editor

推理与编辑分工:同一模型自己跟自己配对也涨分(Sonnet 77.4→80.5)。角色拆分的收益有 benchmark 级证据,但主要解决"编辑格式遵从"问题,Claude Code 原生编辑已消化;保留其原理:**验证/生成分工的收益 > 执行拆分**(与 Cognition 数据一致)。

## 汇总:对 seed-kit 的增量结论

**新增候选提案**(STRONG_MODEL_RESEARCH 八条之外):

| # | 机制 | 来源 | 判据归类 |
|---|---|---|---|
| N1 | 工作发现通道:`seed discover` 落盘途中发现的工作,收口时人裁决 | Beads discovered-from | 盘上机器事实(升值) |
| N2 | 规则上移:review-loop 同类 finding 重复 → 提议沉淀项目规则,人批准 | Anthropic 迁移 rulebook + Every compound | 供给侧闭环(升值) |
| N3 | judge 红样自检:review-loop 的 judge 须证明"能抓故意破坏的产物" | Anthropic 迁移"校验判官" | 激励对抗(永不贬值) |
| N4 | 教训升格阶梯:wiki prose → 项目规则 → 探针/测试,每层问"下次能自动抓住吗" | Every compound + verification loops | 供给侧闭环 |
| N5 | review 家族异模型选项(Oracle 模式) | Amp Oracle | 可选增强,低优先 |

**被外部验证的既有设计**(不动,信心增强):
- `seed done` 真实执行命令的 oracle 设计(对照 /goal transcript-only oracle 的社区批评)
- P1 评分链路防篡改(Ralph 清单"oracle 必须 agent 不可写"+ METR)
- checkbox/盘上可重建队列("done = 文件在盘上"同构)
- 验证侧干净 context 派生 > 执行侧拆分(Amp/Cognition/迁移三方一致)
- gate 守硬事实、好坏走 review 的分层(TDD Guard"机械合规≠质量"实证)

**再次确认的贬值规律**:Amp 删 TODO/杀扩展、Anthropic 删 sprint 构造与 per-sprint 评估、专门化 subagent 在弱模型代失败——"新模型落地时重新审视 harness,剥掉不再承重的部分"(Anthropic 原话)已是行业惯例,seed-kit 的 P0-3 清剪走在同一条线上。
