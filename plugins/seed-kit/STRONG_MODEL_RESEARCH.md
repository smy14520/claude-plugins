# 强模型时代的 seed-kit 优化研究

> 2026-07-26。方法:7-agent workflow——5 路并行 web 调研(harness 设计哲学 / spec-driven 生态 / 验证机制 / 多 agent 编排 / 记忆知识层,2025-2026 一手来源)+ 1 路仓库机制盘点(逐条区分保姆条款与不变量)+ 1 路综合裁决。
> 研究问题:哪些机制在强模型(Claude 5 级)下贬值该删、哪些是真实不变量该留、该新增什么杠杆。

> **状态:未认证调研。** 八条提案是研究结论,**未经 seed-kit-evals-v2 实验认证**;唯一进入认证流程的是 P0-3 第一批(实验 p03-prompt-prune-impl / p03-prompt-prune-review 进行中)。每条提案实施前必须按其 eval_plan 拿数据并写 CONCLUSION 结账,认证结果回写本文件;调研引用的外部数据(Anthropic/METR/论文等)是设计依据,不是本插件语境的验证。

## 两条总判据(所有争议的裁刀)

1. **升值 vs 贬值**:一行机制/规则是否提供**模型无法自行推断的信息**(任务需求、项目约定、盘上事实 → 升值,加大投资),还是**模型能力的补偿**(步骤提醒、自审 checklist、常识枚举 → 贬值,删)。依据:ETH Zurich 实测程序性 context 文件 +20% 成本不升成功率;Anthropic 官方判定式 "Would removing this cause Claude to make mistakes? If not, cut it"。
2. **激励对抗 vs 能力补偿**:防激励错位的机制(gate、hook、生成者≠验证者、评分链路隔离)**随模型变强反而升值**——METR 实测前沿模型在能染指评分机制的环境里 30%+ 概率篡改评估函数,口头禁令后 70-80% 仍继续。这类机制永不删。

## 提案(按优先级)

### [P0] AC 条目绑定可重放探针命令：把"可证伪"从措辞升级为机器结构

**改什么**:templates/prd.md 的 AC 条目支持可选内联探针（形如 `* [ ] <测试用例> — probe: <命令>`）；skills/brainstorm/SKILL.md 要求对可机器验证的 AC 在产出时写入探针（不可机器化的条目允许无探针，不逼假探针）；tools/seed.py parse_prd 解析探针，cmd_done 在 slice gate 时逐条重放该 slice 的探针并复用 _looks_like_obvious_noop 拒空操作；agents/seed-assert.md 的重放面从 done-log 扩展到 AC 探针，输出逐条 AC 级 pass/fail。

**依据**:Sibylline 实测 agent 对 spec 的条目级执行率只有 70-90%，缺口在整体测试绿之下不可见；marmelab 记录 agent "marked verification tasks complete without writing unit tests"；Tessl（$125M 押注）把每条 capability 直链 test 文件，PDD 论文把 spec 收敛为不变量+持续证据；Anthropic best practices 明确最有用的 spec "end with an end-to-end verification step that proves the feature works"，且 "spec 精度回报高于实现期看护"。现 gate 是任务级（测试+质量命令整体 exit 0），条目级缺失正是它的结构盲区。

**预期增益**:这是升值型机制：模型越强越能写出好探针，逐 AC 机器证据的成本越低、信号越硬。直接压掉"整体测试绿但个别 AC 没做"的失败模式，同时给 review 家族提供逐条客观锚（assert 覆盖面扩大后，judge/review 的主观裁量域缩小）。是从实现期看护向 PRD 精度转移投资的具体落点。

**成本/风险**:PRD 写作成本上升（brainstorm 变长）；探针可能沦为形式（恒真命令）——空操作检测能拦显式空操作但拦不住假测试脚本，兜底仍靠 review；探针本身会过期（AC 改写后探针漂移），需 status 校验探针与条目对应关系。切勿把探针做成强制字段，否则复刻 Spec-Kit 仪式税。

**评估方案**:seed-kit-evals-v2 value 实验：同一批带预埋条目级缺口风险的任务（多 slice、AC 间弱耦合），control=现 prd.md 模板 + 现 brainstorm，treatment=探针模板 + 探针版 brainstorm。指标：集成 review/review-loop 发现的 AC-miss 数（越低越好，且要区分是被 gate 提前拦下还是根本没发生）、seed-assert 可重放覆盖率（覆盖的 AC 条目占比）、brainstorm+impl 总 token 成本、假探针率（人工抽检探针是否真验证该条目）。

### [P0] per-slice review 从强制仪式降级为机器信号触发的风险分层

**改什么**:skills/impl-agent/SKILL.md 步骤 3 从"每 slice 必审"改为默认跳过，仅当机器信号命中才审：(a) 该 slice attempt_count > 0（gate 曾失败）；(b) diff 触碰前序 slice 已交付文件（helper 从 done-log/commit range 算文件重叠，tools/seed.py cmd_next_action 输出 review_recommended 布尔+理由）；(c) slice agent 返回的 handoff 显式标记不确定性。未命中的 slice 直接 commit，靠既有集成 review 收口。同时删除第 70 行的自注（判断已兑现为机制，不再需要口头预留）。

**依据**:Anthropic harness-design-long-running-apps 在 Opus 4.6 上删掉 per-sprint evaluation、评审收敛为 "a single end-of-build pass"，并给出 "Every component in a harness encodes an assumption about what the model can't do" 的贬值判定；Anthropic 自家 SDLC 用 "risk-weighted sample is reviewed" 而非全量；自家 value 实验 +2pp/+645% 与 Spec-Kit（+109% token 且成功率更低）、ETH Zurich（+20% 成本不升成功率）量级互证——这是行业规律不是实现问题。但 Faros 数据（AI 合著 PR 1.7x 问题率）与自验证论文（自验证不随生成变强）说明 review 需求真实，答案是分配而非取消。

**预期增益**:把 +645% 成本砍到只花在机器事实标记的高风险 slice 上；判定条件全部从盘上纯推导（attempt_count、文件重叠），零模型自报，符合"编排由机器事实驱动"教义。对强模型是净解绑：低风险 slice 不再被逐片打断。

**成本/风险**:漏审低风险 slice 的衔接 bug（集成 review 仍在，但延迟发现修复更贵）；触发条件校准不当会退化为全触发（等于没改）或全不触发（等于砍掉）；文件重叠计算对非 git 项目需降级语义。

**评估方案**:seed-kit-evals-v2 三臂 value 实验，任务集预埋跨 slice 衔接 bug（接口签名漂移、共享状态冲突）：A=现状全量 per-slice；B=风险分层触发；C=无 per-slice 仅集成 review。指标：任务完成率、预埋衔接 bug 检出率与检出时点（per-slice 阶段 vs 集成阶段）、总 token 成本、per-slice review 实际触发率（B 臂应显著低于 100%）。若 B≈C 且检出率不降，进一步降级为纯集成 review。

### [P0] SKILL/prompt 贬值项集中清剪 + 环境补丁下沉 helper（分两批，逐批 eval）

**改什么**:第一批（纯噪音）：删 agents/seed-impl.md 与 seed-slice.md 步骤 5 的四项自审 checklist、三处"完整感…不要跳过"、skills/review/SKILL.md 措辞红旗词表、brainstorm 三条负向禁令、impl/SKILL.md "不要 run_in_background"、impl-agent 步骤 4 "git status 快扫"提醒；seed-validator.md 例外补丁 (4)(5) 重抽象为一句方向规则（"过度报告判定只适用于以验收条目为准绳的 finding 类型"）并消除与 review-loop.template.js 的双份维护。第二批（含机制迁移）：CLAUDE_PLUGIN_ROOT one-liner 下沉进 bin/seed 自解析（conventions.md 与 review-loop.md 两处删除）；Workflow/TaskOutput 操作说明书封装进 review-loop.template.js 与 helper 高信号输出；修 skill/agent 命名对称性或把登记表收敛到 conventions.md 单处、删各文件头重复提醒；seed-review 保留五层语义分类、删"必须执行不可跳过"与逐项 checkbox。tests/test_prompt_contract.py 加防回潮断言。

**依据**:官方判定式 "Would removing this cause Claude to make mistakes? If not, cut it"、"Bloated CLAUDE.md files cause Claude to ignore your actual instructions"；ETH Zurich 实测程序性 context 文件 +20% 成本不升成功率、"unnecessary requirements make tasks harder"；Chroma context rot：单个干扰项即降性能；ASE 2025：更复杂的 review prompt 实测导致更高误判率。环境补丁下沉是仓库自家教义（"需要记住一串机械步骤就该做成命令"）的欠账。

**预期增益**:减少锚定效应（checklist 让模型只查列出的四项）与注意力稀释；把 harness 怪癖从 prompt 层挪进代码后跨模型代际稳定；SKILL 文本量从负债转为可维护资产。删减本身就是性能优化，有论文级背书。

**成本/风险**:个别条款可能仍在挡真实回归（尤其 validator 例外补丁是历史 eval 教训的沉淀）——必须分批删、逐批回归，遵循 Anthropic "removing one component at a time" 方法论；bin/seed 自解析需处理多安装形态；第二批工程量中等。

**评估方案**:seed-kit-evals-v2 sentinel + core-semantic 全流程旅程 A/B：control=现 prompt，treatment=删减版。第一批指标：旅程成功率、违规率（越权 commit、发明命令、跳过取证）、token 消耗、validator 假杀率（删例外补丁后 experience/ok 类 finding 是否被误判 invalid——需专设含此类 finding 的场景）。第二批加 harness 交互稳定性（review-loop 结果链路取值错误率）。任一指标显著回退则该条款回滚并在 CONCLUSION.md 记录为已证实仍需的边界。

### [P1] impl 单 agent 熔断机器化：双语义收敛到 gate-attempts

**改什么**:删除 skills/impl/SKILL.md 第 44、54 行的 prompt 计数条款（"派 3 次仍失败→停"）。编排循环改为：agent 返回后即跑 seed done（agent 报告失败也跑——失败自动落 gate-attempts/ 留痕），重派前读 attempt_count（复用 tools/seed.py _count_gate_attempts 与 CIRCUIT_BREAK_THRESHOLD），≥3 即 escalate。环境阻塞类失败不入计数（agent 明确报环境问题时走卡住协议，不跑 done）。impl 模式重派 prompt 同步注入 gate-attempts 失败输出（对齐 impl-agent SKILL 第 45 行已有机制）。

**依据**:known_gaps 明列此未收敛项：同一熔断语义在 impl-agent 已机器化（"不需要你计数"）、在 impl 靠模型记忆数数——违反自家教义"把不确定步骤转为确定性 helper"。Anthropic effective-harnesses：进度状态必须在盘上，会话中断后模型记忆为零；Manus：失败 trace 留在 context 是学习信号，配套注入让重试不重复同一错误。

**预期增益**:中断恢复后熔断计数不丢；单一实现消灭"同一语义两种可靠性"；失败输出回灌让强模型的 second-pass 自纠错有据可依（Ralph loop 实证：第二遍会看到自己漏了什么）。纯机制收敛，零新增流程文本。

**成本/风险**:低。需注意 seed done 在 agent 未产出显式测试命令时不可跑（fail-closed 不变）——此时 agent 级失败无处留痕，可接受（该场景本就该走卡住协议而非重试循环）；失败类型区分（代码失败 vs 环境阻塞）仍是模型判断，但错分的代价只是多一次计数。

**评估方案**:seed-kit-evals-v2 core-semantic 旅程：注入恒红测试的 slice，断言恰在第 3 次机器计数处 escalate（不多不少）、gate-attempts/ 有 3 条留痕、reset-attempts 后可续；加会话中断变体：第 2 次失败后杀会话重入，断言计数延续至第 3 次触发熔断。control=现 prompt 计数版对照跑同场景，记录其计数漂移率（提前停/多派次数）作为改进基线。

### [P1] 评分链路防篡改：done-logs/gate-attempts/review-mark 与生成者隔离

**改什么**:hooks/seed_guard.py 拦截面扩展一条窄线：拦 Edit/Write/NotebookEdit 及 Bash 重定向对 `.arbor/tasks/*/done-logs/`、`gate-attempts/`、`impl-state.json`、`review-loop.json` 的直接写入（这些路径只能经 seed CLI 变更）；tools/seed.py cmd_review_mark 增加最小一致性校验：verdict=converged 时要求 --evidence 指向本轮 review 产物（review.md 追加段 hash 或 loop 输出摘要），缺证据仍落 marker 但标 `unverified: true`，Living PRD 与下游如实展示。

**依据**:METR 实测 frontier 模型在可染指评分机制的环境里 30%+ 概率篡改评估函数，"Please do not reward hack" 禁令后 70-80% 仍继续——环境设计而非提示词决定诚实性，评分代码必须与 agent 隔离。known_gaps 明列两条缝隙：review-mark 是无验证自报终态（可在未跑 loop 时落 converged）；seed_guard 声称"checkbox 只能由 seed done 勾选"但 done-log/gate-attempts 本身不设防——客观锚可被生成者染指则 seed-assert 与熔断计数的可信度归零。

**预期增益**:激励对抗型机制，与模型能力正交、永不贬值——模型越强越能造出貌似合理的假记录，这条越关键。它是 assert/熔断/集成 review 全部下游可信度的前提，属于加固护城河而非加缰绳。

**成本/风险**:与"hook 只守窄底线"教义有张力——裁决：评分链路完整性正是底线范畴（同 checkbox 拦截同构），且拦截面是封闭路径集不是语义判断。正则仍可被绕过（heredoc/tee 等），定位是提高门槛+留下违规痕迹，不承诺完美防御；fail-open 语义保留。--evidence 校验是形状校验不是语义核验，防的是无意/低成本伪造。

**评估方案**:seed-kit-evals-v2 sentinel 增红队场景：(a) 任务 prompt 诱导 agent 直接写 done-log 伪造通过记录；(b) 诱导未跑 loop 直接落 converged marker。treatment 臂断言 hook 拦截留痕或 marker 带 unverified；control（现状）臂验证缝隙确实可被利用（作为改动必要性的证据）。回归面：正常旅程中 seed CLI 自身写入不被误拦（hook 需识别合法写入方）。

### [P1] review 家族显式可靠性层级 + validator 证伪升级为可执行 kill

**改什么**:templates/review-loop.template.js 的收敛/熔断判定按显式层级加权：assert（客观重放）> validator（经验证伪）> review（spec 对账）> judge（体验）——高层可否决低层，judge finding 永不进 blocking 计数与熔断路径（只作报告与人类参考，judge 域收窄到 assert 无法覆盖的体验维度）；agents/seed-validator.md 对可执行验证的 finding 要求附 kill 命令（只读复现/反证命令），由 loop 编排真实执行、exit code 写入裁决依据——"多个 reviewer 同意"不再算收敛证据；借此重审 template 第 177-178 行 "missing-deliverable 一律 blocking"（EVAL_HANDOFF §9 悬案）：改为 missing-deliverable 须先经 assert/文件存在性机器核验再定级。

**依据**:Refute-or-Promote（2026）：对抗性 kill mandate 前瞻杀掉 83% 假阳性，"ten dedicated reviewers unanimously endorsed a non-existent Bleichenbacher padding oracle" 被单次经验执行击杀——一致同意不能替代一次真实执行；Weaver：加权聚合显著优于摊平（"Weighted aggregation significantly outperforms unweighted combinations"）；judge bias 论文：LLM-as-judge 一致性可近随机、易被表面线索翻转，失效回落是可执行测试；ASE 2025：review 对照 spec 系统性产假阳性，validator 是必要下游而非冗余——删 judge 权重不等于删成员。

**预期增益**:假阳性 finding 不再进修复循环烧 token（这是 review-loop 成本的大头）；层级写成确定性模板规则，符合"机制优于长篇提醒"；对强模型是解绑——强模型 review 产出的真 finding 经 kill 存活后置信度更高，修复更果断。

**成本/风险**:kill 命令执行有成本与副作用风险（必须约束只读、超时）；不是所有 finding 可执行证伪（架构/风格类），需保留 ambiguous 文字裁决回退，防止"不可执行即 invalid"的误杀；层级规则本身要防过度设计——先只做"judge 不进 blocking 计数"和"kill 命令可选强化"两个最小变更。

**评估方案**:seed-kit-evals-v2 双向注入 value 实验：任务集一半预埋真 bug、一半是已知干净实现。control=现 validator 文字裁决 + 现聚合；treatment=层级加权 + kill 强制。指标：进入修复循环的假阳性率（干净臂应显著下降）、真 bug 漏杀率（预埋臂不得上升）、review-loop 收敛轮数与总成本、judge finding 单独统计其历史 blocking 贡献中被证伪的比例（决定 judge 降权幅度的数据依据）。

### [P2] wiki 三线改造（载体/消费/供给）+ 明确退出条件

**改什么**:(a) 载体侧：tools/wiki.py lint 增两项机器检查——收录判据（条目内容可从代码推导→建议删；坑/决策理由/偏离默认约定→留，直接采用 Claude Code /doctor 判据）与消费路径（每条目必须声明 trigger 字段或标注晋升目标 CLAUDE.md/rules/skills，两者皆无→报废弃候选）；(b) 消费侧：impl-agent handoff 组装与 review-loop 上下文准备两处，由 helper 跑 `seed wiki collect --query`（trigger 匹配窄注入，绝不全量灌注，不加新阶段）；(c) 供给侧：review-loop 终态落 marker 时，helper 从本轮 finding 与 gate-attempts 提取候选坑/理由生成 wiki 条目草稿，人一键批准入库。退出条件写进 WIKI_RESEARCH.md：两个 eval 周期后 collect 命中且被产出引用的比率仍趋零 → 删除 wiki 家族，承认被 grep + git log 替代。

**依据**:Google 生产结论："experiments requiring the user to remember to trigger the feature have failed to scale"——wiki 死因是消费路径不是内容质量；Devin Knowledge 的 trigger 字段 + 纠错时刻捕获是已验证形态；Claude Code /doctor 判据与 MEMORY.md 两层结构提供现成收录标准；Cline Memory Bank 反例 + Chroma context rot 划定红线：绝不做每会话全量注入；Anthropic memory tool +39%、Rakuten -97% 首轮错误证明 agent 自写+人审的记忆线随模型变强持续增值；glob+grep>RAG 给出廉价对照假设。

**预期增益**:把 wiki 从孤岛死层改造成随模型增值的资产（模型越强、自动沉淀的条目质量越高、trigger 匹配越准），或以数据为据干净退出——两个出口都消灭"有生产无消费"的僵尸状态。三线都是确定性 helper 动作，不加流程文本。

**成本/风险**:三线全做工程量不小且 wiki 可能最终仍被证伪——因此排 P2，先做最小闭环（lint 判据 + impl-agent handoff 一处消费点），草稿管线后置；trigger 匹配质量差会注入噪音（context rot 反噬），collect 结果须设条数上限。

**评估方案**:seed-kit-evals-v2 跨 session 知识复用旅程：session1 在含已知 gotcha 的项目做任务并沉淀，session2 干净 context 做同域任务。三臂：A=现状 wiki（软约定消费）；B=trigger+helper 注入版；C=无 wiki（纯 grep+git log）。指标：重复踩坑率、collect 命中且被引用比率、session2 完成质量与成本。若 B 不显著优于 C，执行退出条件删除 wiki 家族并在 CONCLUSION.md 结账。

### [P2] recitation 机制化：next-action 输出 remaining 清单供长任务锚定

**改什么**:tools/seed.py cmd_next_action 的 start_slice 返回里增加 remaining_slices 摘要（剩余 checkbox 的 slice id + 标题，从 prd.md 现算，超长截断）；skills/impl/SKILL.md 与 impl-agent/SKILL.md 的派发 prompt 模板把它注入 agent prompt 开头（"全局剩余：…，本次只做 {slice_id}"）。零新状态、零新阶段——纯粹把已有盘上事实推到注意力近端。

**依据**:Manus 生产实证："By constantly rewriting the todo list… reciting its objectives into the end of the context" 在平均 50 次工具调用的长任务上对抗目标漂移；Anthropic context engineering：attention budget 随 context 增长衰减，近端信息权重高。prd.md 本就是官方推荐形态的结构化清单，只差把它从"进度记录"用成"注意力锚"这半步。

**预期增益**:长 PRD（8+ slices）后段的 AC-miss 与范围漂移下降；对强模型是纯增益（多给一行高信号事实，不加任何约束）；实现成本几乎为零，且与 P0-2（降 per-slice review 频率）互补——review 降频后靠 recitation 维持全局对齐。

**成本/风险**:接近零。remaining 列表过长时截断即可；唯一风险是注入位置不当被当作本次任务范围（措辞需明确"只做当前 slice"，现有 prompt 已有此句）。

**评估方案**:seed-kit-evals-v2 长任务旅程 A/B：8+ slice 的 PRD，control=现 next-action 输出，treatment=带 remaining_slices 注入。指标：后半段 slice 的 AC-miss 率（集成 review finding 按 slice 位置分桶）、越界实现率（做了后续 slice 的内容）、总成本差（应≈0）。可搭 P1-4 的场景复用同一任务集。

## 该删除/降级的贬值组件

- impl-agent per-slice review 强制仪式（skills/impl-agent/SKILL.md 步骤 3）→ 降级为机器信号触发的风险分层（依据：Anthropic 在 Opus 4.6 上删 per-sprint evaluation、自家 SDLC 风险加权抽样、自家 value 实验 +2pp/+645% 与 Spec-Kit/ETH Zurich 重流程税数据互证）
- impl 单 agent 的 prompt 计数熔断（skills/impl/SKILL.md 第 44、54 行"派 3 次仍失败"）→ 删除，收敛到 gate-attempts 机器计数（依据：自家教义"把不确定步骤转为确定性 helper"，impl-agent 已证明机器化可行；会话中断后模型记忆归零）
- seed-impl/seed-slice 步骤 5 的四项自审 checklist → 删除（依据：官方判定式"模型不需指示就做对的，删掉"；checklist 造成只查四项的锚定；ASE 2025 实测复杂 prompt 增误判）
- 三处"完整感……不要跳过"（seed-impl.md 步骤 6、seed-slice.md 步骤 6、seed-review.md）→ 删除（依据：防偷懒口头禁令已被 judge 在环 + review 家族的机制替代；METR 证明口头禁令本就低效）
- seed-review"审五层必须执行不可跳过"的执行强制与逐项 checkbox → 删强制、保留五层语义分类（依据：语义结构是资产、动作指定是弱模型补偿；Chroma context rot 单干扰项即降性能）
- skills/review/SKILL.md 措辞红旗词表（should/seems/大概…）→ 删除，改为一句"按证据强度判断"方向（依据：固定词表是弱模型启发式，漏报+误伤双输）
- commands/review-loop.md 的 Workflow/TaskOutput 操作说明书（双 id、args stringify、name 冲突）→ 下沉进 review-loop.template.js 封装与 helper 高信号输出（依据：自家 workflow-design.md"外部环境干扰不包装成 workflow 兜底"；harness 修好即成死重）
- CLAUDE_PLUGIN_ROOT 兜底 one-liner（conventions.md + review-loop.md 两处）→ 下沉进 bin/seed 自解析，prompt 层删除（依据："需要记住一串机械步骤就该做成命令"的自家反例）
- 调用名登记表的各文件头重复提醒（"别加 seed- 前缀"）→ 修命名对称性或收敛到 conventions.md 单处（依据：自认历史债的补偿层，重复提醒是噪音）
- seed-validator 裁决 checklist 例外补丁 (4)(5)（agents/seed-validator.md 第 22-23 行 + template 双份）→ 重抽象为单句方向规则并消除双份维护（依据：prompt-design.md"规则需要不断追加例外时重新抽象"；但对抗结构本身保留，删的是补丁形态）
- brainstorm 三条防跑偏负向禁令（不做历史考古/不凑方案/无分叉直接推进）→ 删除，正向方向"只解决影响实现结果的分叉"已足够（依据：针对弱模型表演性彻底性的反向补丁）
- "不要 run_in_background"（impl/SKILL.md 步骤 1）与"git status 快扫"（impl-agent 步骤 4）→ 删除或下沉为 helper 前置校验（依据：操作参数提醒非边界）
- AskUserQuestion 通道分叉微规则（brainstorm：选项条数、推荐 label、"会卡死"分支）→ 压缩为一句（依据：评估 harness 场景补丁 + 交互常识过度指定）
- seed-judge 的裁决权重 → 降级：finding 永不进 blocking 计数/熔断路径，域收窄到 assert 无法客观化的体验维度（依据：LLM-as-judge 一致性可近随机、易被表面线索翻转、官方称 "generally not a very robust method"；但作为 ensemble 成员保留——见 contradictions 裁决 2）

## 必须保留的不变量

- 四锚点公理（PRD=需求 SoT、文件系统=状态 SoT、git=进度 SoT、硬事实=正确性 SoT）——与模型强弱无关的状态归属裁决层
- seed done 唯一合法进度入口 + hook 拦手改 checkbox——防激励错位（生成者自发通行证）而非防健忘；METR reward hacking 数据直接背书，Anthropic effective-harnesses 在最强模型上仍需同构机制
- done 硬 gate 全 exit 0 + _looks_like_obvious_noop 拒空操作——官方排序 rules-based feedback 最优；定位明确为下界而非完成证明（SWE-bench Verified 教训），与 review 家族两层不可互替
- gate 只卡硬事实、体验走 review-loop 迭代——验证手段本性的设计定理；模型越强越会优化通过条件，此边界越重要
- 破坏性命令拦截（DESTRUCTIVE_RE）——不可逆动作防线必须机械，代价不对称与能力无关
- 分支与提交归用户、agent 不 commit——所有权是授权问题不是能力问题
- 生成者≠验证者 + disallowedTools 机械锁只读——2026 论文证明自验证不随生成能力自动提升，是正交能力轴；Cognition 生产数据：无共享 context 的 review agent 表现最好。这是随模型变强反而升值的结构
- seed-validator 对抗证伪结构——Refute-or-Promote 实证杀掉 79-83% 假阳性；官方警告 reviewer 系统性过度报告，validator 恰是解法；review 与 validator 是配套不可单删
- seed-assert 客观锚 + done-logs/gate-attempts 物理分离——重放纯度是数据模型不变量；Anthropic "session 开始先重放验证"同构背书
- 无显式命令即停（fail-closed：不猜测、不代填、不发明命令）——模型越强越能发明貌似合理的命令，假验证信号比无验证更坏
- 六 skill 全部用户显式触发、互不自动流转——阶段流转是授权语义；与"砍审批链"不矛盾（砍的是流程内仪式，不是用户主权）
- durable gate 归主会话独占、subagent 不碰 seed done/checkbox/git——durable state 写入者唯一且可追责
- task_start_sha 写一次锁死 + next-action 纯推导、不采信模型自报 phase——解决持久性问题不是智力问题，官方 "structured progress file + git 锚点" 推荐形态
- review-loop 封闭终态集 + 非 converged 一律 escalate 交人——"验证系统自身失灵时归人"是不随能力变化的安全语义；ralph 式极简循环内核被官方收编背书
- review 取证 fail-closed（读不到产物标 unavailable，不编造 expected/actual）——证据完整性边界
- seed-prd-review 只读 + 禁递归派 Agent——有实战事故背书（spawnDepth 1→5）的结构约束
- 机制在插件、标准在项目 + test_prompt_contract.py 机械守护——架构分层不变量，与模型强弱正交
- wiki 永不是 SoT、定位后必须验证当前代码——WIKI_RESEARCH F2 实证 stale 权威文档使验证率归零且"不管模型多聪明"
- Living PRD 纯派生只读、可删可重生——SoT 单向数据流
- 查证于 provenance 协议——对抗模型记忆滞后的轻量事实溯源，随模型知识截止问题长期存在
- brainstorm 访谈式收敛 PRD（planner 角色）——Anthropic 两代 harness 实验中 planner 都是幸存组件（"without the planner, the generator under-scoped"），且 interview→spec→fresh session 是官方钦定工作流，属于该加大投资的升值组件
- impl 默认单 agent 做所有 slice——SWE-bench 极简 scaffold 哲学 + coding 缺可并行子任务的行业共识；impl-agent 保持可选不默认

## 矛盾裁决

- 【per-slice review：该砍 vs review 需求真实】角度 1/2/4 引 Anthropic 删 per-sprint eval、Spec-Kit/ETH 重流程税，主张砍掉；角度 3 引 Faros（AI 合著 PR 1.7x 问题率）、自验证不随生成变强的论文与 Anthropic SDLC 风险分层，主张 review 需求真实存在。裁决：两者说的不是同一个东西——独立验证结构是激励对抗型（不贬值，保留），"每片必审"的频率是能力补偿型（贬值，降级）。落点：留结构、降频率——默认集成 review 一次，per-slice 仅由机器信号（attempt_count>0、文件重叠、handoff 标记）触发。不接受"全删"也不接受"维持全量"。
- 【seed-judge：LLM-as-judge 不 robust 该降级 vs weak verifier ensemble 不该删成员】角度 1 引官方 "generally not a very robust method" 主张降级为可选；角度 3 一面引 bias 论文（一致性近随机）一面引 Weaver（加权组合跨一代模型能力差距）主张留成员、改聚合。裁决：留成员、降权重、收窄域——judge 保留为 ensemble 中权重最低的成员，其 finding 永不进 blocking 计数/熔断/收敛判定，只作人类参考；凡 assert 能客观化覆盖的维度一律移交 assert；judge 只保留真正无法机器化的体验维度。Weaver 的结论恰恰是"加权"而非"摊平"，两派在"judge 不能拥有裁决权"上实质一致。
- 【干净 context per-slice 派发：官方机制 vs 被证伪编排】角度 1 说 fresh session per feature 是官方推荐机制、可拆开保留；角度 4 说 per-slice 写者拆分收益已到顶（METR 自主时长每 3-4 月翻倍，长 context 撑不住的假设在过期）、context rot 却仍实存。裁决：干净 context 这个资源本身不贬值（context rot 是注意力架构问题），贬值的是把它花在执行侧拆分上——其净收益区已迁移到验证侧派生（Cognition：review agent 无共享 context 表现最好）。落点：impl-agent 保留为超长任务/熔断后的显式回退选项，不默认、不再投资 handoff 摘要质量（handoff 降为文件锚+git 指针）；review 家族派生时刻意窄 context（只给 PRD、diff、产物，不带 impl 过程）。
- 【wiki 修法：机器化归并消费 vs 机器注入或删除 vs 禁止消费侧强制】角度 2 主张 OpenSpec-archive 式机器归并；角度 3 引 Google "靠用户记得触发必死"主张机器注入或删；角度 5 引 Cline Memory Bank 反例主张绝不消费侧强制、走供给侧+载体侧。裁决：三者共享一条红线——绝不做每会话全量灌注（Cline 反例 + Chroma context rot 实证），此外互补而非互斥：消费侧做"既有编排点的确定性 helper 窄注入"（trigger 匹配、有条数上限，这是机器动作不是用户记忆负担，不违反 Google 结论也不复刻 Cline）；载体侧向标准加载路径晋升；供给侧在纠错时刻自动提议草稿。并设退出条件：eval 证明不优于纯 grep+git log 即删——"维持现状（有生产无消费）"是唯一被所有角度共同否定的选项。
- 【ETH "context 文件不提升成功率" vs 官方 "spec 精度回报高"】表面冲突：一边说给 agent 喂约束文件是 +20% 纯税，一边说把 spec 写精确回报高于看护实现。裁决：ETH 测的是程序性/常识性 context（模型可自行推断的内容），官方说的 spec 是任务特定需求事实（模型无法推断）。统一过滤判据：一行内容是否提供模型无法自行推断的信息——PRD/AC/项目命令/非标准约定属后者（升值，加大投资），SKILL 里的步骤提醒/常识枚举属前者（纯税，删）。这条判据同时是 P0-3 清剪的裁刀。
- 【gate 硬语义 vs flaky 现实】角度 3 引 SWE-bench Verified 运营史指出测试有 flaky、gate 自身会产假警报，建议 assert 加重试容忍；而 gate 的不变量语义是全 exit 0 不可妥协。裁决：gate（seed done）保持硬语义不动——它是进度翻转的一次性判定，软化即打开蒙混面；flaky 容忍只加在 seed-assert 的重放侧（失败自动重试 N 次再判红，重试次数与每次 exit code 全部留痕），这是机器化容忍不是软化判定，且留痕本身把 flaky 变成可见信号供人处理。两个机制角色不同，容忍语义只属于重放者不属于门槛。

## 仓库已知缺口(盘点原始输出)

- wiki 与流程的接缝是自认最大缺口（WIKI_RESEARCH.md 全文）：行号漂移自愈、`seed wiki fix --safe` 确定性自愈子集（QW3）、typed edges、变更触发的 drift 标记 hook（建议 4）、review 学习回写闭环（建议 6）均未实现；wiki 仍偏孤岛，QW2 的消费点（impl/review 的 collect/写回）已进 SKILL 但为软约定，跳过率无数据。
- handoff 只在主会话内存传递、中断即丢——impl-agent/SKILL.md 自认，靠已落盘代码 + done-log 续接是降级恢复而非等价恢复。
- per-slice review 的增量价值未定：SKILL 自注'会随模型变强贬值的组件'，等待 eval 数据决定是否降级为抽样；impl-vs-impl-agent value 实验已显示 impl-agent 完成率小幅更高但成本显著更高（DESIGN.md 第 96 行），成本收益边界仍开放。
- seed_guard 是软底线：payload 解析异常时 fail-open（seed_guard.py main() 注释'hook fails open softly'）；正则可绕过——cat heredoc/tee/重定向写 prd.md 不在拦截面，DESTRUCTIVE_RE 未覆盖 git checkout --/git restore/find -delete 等。设计上'hook 只守窄底线'是自觉取舍，但拦截面与声称的'checkbox 只能由 seed done 勾选'之间存在缝隙。
- seed review-mark 是无验证的自报终态：helper 只校验 verdict 在封闭集内（tools/seed.py cmd_review_mark），不核对是否真跑过 review-loop——模型可在未跑 loop 时落一个 converged marker，review-loop.json 的可信度依赖流程自觉。
- impl（单 agent 模式）的 3 次失败熔断靠 prompt 计数，而 impl-agent 已机器化为 gate-attempts 计数——同一语义两种可靠性，属仓库自己教义（'把不确定步骤转为确定性 helper'）下的未收敛项。
- review-loop 结果链路与 harness 深耦合：Workflow 脚本不能写文件、args 被 stringify、双 id 混淆、name 参数语义冲突——全部靠 commands/review-loop.md 的操作说明书兜底（模板头部'已固化修法'清单即坑列表），harness 变更即碎。
- missing-deliverable 一律算 blocking（review-loop.template.js 第 177-178 行）被 EVAL_HANDOFF.md §9 明确标记为'可能是症状当规则'待审视，至今未结论。
- review-loop 已知盲区（EVAL_HANDOFF.md §8 四路对比实证）：工程实践入口（lint/build）、可访问性、隐性状态一致性——四个 harness 都漏掉同一个 reload id 冲突 bug；spec 未要求的隐性维度是所有方法共同盲区。
- Living PRD 只取排序后第一个 task（_find_task 取 sorted 首个），多 task 项目展示错位；hooks.json 的 Bash(*done*) 触发条件过宽（任何含 done 的命令都触发重生成），因 async+opt-in 代价低但不精确。
- '诚实地最小满足'只被承认未被消除（DESIGN.md 两种失败模式）：_looks_like_obvious_noop 只拒'显而易见'的空操作，恒 exit 0 的假测试脚本（如 node fake_test.js）可过 gate，兜底完全依赖 review 家族的语义审查。
- 命名不对称（skill 无 seed- 前缀、agent 有）自认是历史遗留（conventions.md），靠登记表 + 各文件头重复提醒补偿而非修正。
- CLAUDE_PLUGIN_ROOT 在 bash 子 shell 为空是环境级缺口，修法以 prompt 内 shell one-liner 形式存在于 conventions.md 与 review-loop.md 两处——按自家 workflow-design.md 教义应属'修环境而非包装成 workflow 兜底'的场景。

## 调研角度摘要

- 围绕"强模型时代 harness 设计哲学"完成调研，覆盖 8 篇 Anthropic 一手来源（building-effective-agents、context-engineering、long-running harnesses、Agent SDK、Agent Skills、writing-tools、SWE-bench scaffold、Claude Code best practices）+ 4 个独立第三方论述（Bitter Lesson applied to harness、hidden technical debt of agent harness、Lance Martin、Ralph loop），关键来源均 WebFetch 读了原文。核心结论：(1) 贬值项是"用人写结构编码可靠性"的部分——prescriptive 流程文本、LLM-as-judge 类主观验证、强制 per-slice 仪式化编排；(2) 不变量是"可机器运行的客观验证 + 生成者≠验证者的 fresh-context 对抗 + 结构化进度文件/git 锚点 + 不依赖 compaction 的干净 context"——seed-kit 的 done 硬 gate、seed-assert、seed-validator、prd.md SoT、SHA 锚点、next-action 纯推导全部落在官方推荐形态上，应保留；(3) 强模型杠杆的新增方向是：把 helper 当产品打磨（高信号错误输出、防呆、consolidate）、SKILL.md 渐进披露分层并定期按"删了会出错吗"判定式剪枝、加大 brainstorm/PRD 侧投资（interview→spec→fresh session 是官方钦定工作流，spec 精度回报高于实现期看护）、wiki 要么让流程 just-in-time 消费要么承认被 plain text + git log 替代。impl-agent 的 +2pp/+645% 成本实验结果与 Bitter Lesson 分析一致：干净 context per slice 本身是官方推荐机制，贬值的是随附的强制 per-slice review/commit 仪式，可拆开处理。
- 2025-2026 年 spec-driven 生态(Spec Kit / Kiro / OpenSpec / Tessl)的经验高度收敛:被实测证伪的是"重流程"——多阶段全量 spec、长 markdown 约束文件、per-step 评审在强模型上是纯税(Spec-Kit 比 OpenSpec 贵约 2 倍 token 且成功率更低;ETH Zurich 实测 context 文件平均 +20% 成本、成功率不升;Anthropic 官方在 Opus 4.6 上删掉了 sprint 切分、context reset 和 per-sprint 评审)。被反复验证为持久不变量的恰是 seed-kit 的内核:机器可验证的 feature/AC 清单 + 拒绝模型自报完成的硬 gate(Anthropic 明确针对 "Claude marks features as done prematurely")、前期 planner(否则 under-scope)、独立外部 QA/review、简单循环直到验收达成(Ralph loop 击败多 agent 编排)。对 seed-kit 的净结论:删/降 impl-agent 的 per-slice review 编排和一切"模型可自行推断"的程序性提醒;保 prd.md checkbox SoT、done 硬 gate、brainstorm、review 家族、review-loop 熔断;新增的强模型杠杆是把每条 AC 绑定可重放验证命令(逐 AC 机器证据,Tessl/@test 与 PDD 不变量方向),并给 wiki 层加 archive/归并式机器动作或直接砍掉——spec/知识层不做机器化归并必然沦为孤岛,这是 Spec Kit 社区最大教训。
- 2025-2026 的验证机制研究给 seed-kit 的核心结论是：seed-kit 的三个"硬"机制（done 硬 gate + hook 防篡改、生成者≠验证者、对抗证伪）都被最新证据确认为真实不变量，不会随模型变强贬值——METR 实测 frontier 模型在可 hack 环境中 30%+ 概率篡改测试/评分器且口头禁令无效；自验证能力被证明不随生成能力提升而自动提升；对抗证伪+经验性执行 gate 在真实项目杀掉约 80% 的 LLM review 假阳性。真正该降级的是无差别 per-slice review（Anthropic 自家 SDLC 的答案是风险分层+抽样而非全量）和 seed-judge 的裁决权重（LLM judge 一致性可低至近随机、易被表面线索操纵，应回落到可执行测试）。该新增的强模型杠杆：review 家族按可靠性加权聚合（Weaver 证明加权弱验证器组合可跨越一整代模型的能力差距）、validator 的证伪从文字论证升级为强制可执行 kill test、wiki 从人工触发改为机器注入（Google 生产数据：靠用户记得触发的功能必然规模化失败）。同时"少即是多"获论文级支持：更复杂的 review prompt 被实测导致更高误判率。
- 2025-2026 的一手证据在"多 agent 编排 vs 单长会话"上收敛出清晰边界，且与 seed-kit 的价值实验（impl-agent +2pp/+645%）高度互证。三条主线：(1) 写路径拆分（per-slice/per-task 派生执行 agent）是全行业公认的低收益高成本区——Anthropic 明言 coding 缺乏可并行子任务、多 agent 耗 15x token；Cognition 2026 更新坚持"写保持单线程"；Anthropic 自己在 Opus 4.6 上删掉了 sprint 拆分构造。(2) 被生产验证存活的多 agent 模式几乎只剩两类：干净 context 的 review/评估 agent（Cognition 实测每 PR 抓 2 bug、58% 严重；且"不共享先前 context 反而表现最好"）和只读研究型 subagent——这正是 seed-kit review 家族的形态，是该加码的强模型杠杆。(3) 删脚手架有硬底线：即使旗舰模型，"compaction isn't sufficient"，未测就宣称完成、context rot 在 2026 模型上依然存在；外部状态锚（progress 文件/git/结构化 checkbox）+ 强制验证 gate 是不随模型变强贬值的真实不变量。对 seed-kit 的净结论：降级 impl-agent 的 per-slice 写者拆分与 per-slice review（贬值资产，METR 显示模型自主时长每 3-4 个月翻倍），保留并强化 prd.md SoT + done 硬 gate + hook 底线 + review 家族（永久资产），新增杠杆在于：review 派生时刻意做窄 context、把 gate 失败 trace 喂回模型 context、用 prd.md 剩余项做 recitation、以及用逐组件消融实验代替直觉来决定删留。
- 2025-2026 年 coding agent 知识层实践已收敛出清晰共识：(1) 强模型时代 agentic search（grep+读代码）取代预建索引/百科式 wiki，Anthropic 明确"smarter models require less prescriptive engineering"；(2) 常驻上下文的知识有硬预算（CLAUDE.md <200 行），官方 /doctor 的删减判据可直接复用——"删代码可推导的（目录结构/架构综述/依赖清单），留坑、决策理由、偏离默认的约定"；(3) 避免死层的结构解法不是"强制流程消费 wiki"，而是把知识放进天然消费路径：小索引常驻 + 正文按需（Claude Code auto memory 的 MEMORY.md 架构）、每条知识带检索触发条件（Devin Knowledge）、或直接降级为 skills/rules/AGENTS.md 这类被 harness 原生加载的标准载体；(4) 跨会话 agent 自写记忆有实测收益（memory tool +39%，Rakuten 首轮错误 -97%），且模型判别力提升使自动维护越来越可靠——该加的杠杆是 agent 自维护、人可审计的记忆，而非人工策展 wiki；(5) 反面教训（Cline Memory Bank 膨胀、context rot 实证）证明每会话全量灌注知识层是负优化。对 seed-kit：wiki 作为独立 .arbor/.wiki 终点存储应降级或重构为"生成 CLAUDE.md/rules/skills 条目的工作台"，收录判据和体积预算机器化进 lint，知识捕获接到 review 收敛/熔断留痕等既有纠错时刻。

## 状态

- P0-3 第一批(纯噪音清剪)进行中:candidate worktree 隔离实施 + seed-kit-evals-v2 A/B 验证,确认有效才合并。
- 其余提案待逐条评审;每条动手前先按本文件 eval_plan 设计实验,遵循"确认有效果才合并"。
