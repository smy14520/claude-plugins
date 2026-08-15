# prototype-wayfinder

## Goal

把 mattpocock/skills 的两个能力按本仓库形态落地，走「candidate → 认证 → 合并」全链路，未认证不合并：**prototype**（一次性可玩原型，回答"跑起来才知道"的设计问题）做成 `seed-prototype` agent——brainstorm 体验方向分支被动派发、用户直说"使用 prototype"时主会话语义派发，产物为 `.arbor/prototypes/<slug>/` 自包含单 HTML，verdict 折回访谈；**wayfinder**（大且雾任务的跨会话决策编排）做成 `skills/wayfinder/` + `.arbor/maps/<slug>/` 文件形态——map.md 索引 + 决策票（frontmatter `type`/`status`/`blocked-by` + Question/Resolution），frontier 由新增 `seed map status` 从盘上推导，图清后交棒 brainstorm 收敛。全部实现落在从 main 拉出的候选分支（独立 worktree），main 工作树冻结作实验基线；认证实验在 seed-kit-evals-v2 跑——control = main 基线插件树、treatment = 候选树（纯新增能力，无需消融 pack），deepseek-v4-flash 执行、glm-5.3 评审；CONCLUSION 结账后用户拍板合并，未通过则候选回滚、main 零残留。票与 slice 两套账本严格分离（票不进 gate、不翻 checkbox）。风格沿用现有 skill 的克制：机制优于 prose、helper 只做确定性动作、地图不构成第二套进度。本 task 跨两仓库：候选实现在本仓库，eval 场景与实验产物在 seed-kit-evals-v2 仓库。

## Acceptance Criteria

### [x] S-001 候选分支就位 + seed-prototype agent 与 brainstorm 派发线

* [x] 从 main 拉候选分支（`candidate/prototype-wayfinder`，独立 worktree）；main 工作树恢复到基线状态，此后冻结至实验结束（正向）
* [x] 候选树 `plugins/seed-kit/agents/seed-prototype.md` 存在：frontmatter description 覆盖两类入口（被 brainstorm/wayfinder 编排派发；用户语义点名"使用 prototype"时主会话直接派发），正文含两分支（逻辑走查 / UI 变体切换面板，问题决定形态）（正向）
* [x] seed-prototype 铁律成文：产物为自包含单 HTML（双击或一条命令可开）、默认无持久化、每次交互后展示全量状态、结论折进真代码而原型本体不进交付（正向）
* [x] brainstorm SKILL 体验方向分支含派发条款：形容词吵不出结果的设计问题 → 派 seed-prototype，产物落 `.arbor/prototypes/<slug>/`，verdict 折进访谈结论（正向）
* [x] conventions.md 登记表新增 `seed-kit:seed-prototype`；agent 文档不含栈特定框架词（如 React/Vue/Playwright）（反向）
* [x] 候选树 tests/test_prompt_contract.py 新增断言锁上述合同，全套 pytest 绿（正向）

### [x] S-002 wayfinder skill 本体与 brainstorm 接缝

* [x] 候选树 `plugins/seed-kit/skills/wayfinder/SKILL.md` 定义地图五节（Destination / Notes / Decisions so far / Not yet specified / Out of scope）与票文件格式（frontmatter `type: research|prototype|grilling|task`、`status: open|closed`、`blocked-by` + `## Question` / `## Resolution` 两节）（正向）
* [x] 票执行分工成文：grilling 票走 brainstorm 提问通道（AskUserQuestion 一次一题）；research 票轻调查派 sub-agent 结论写票、重调查建 `.arbor/research/<topic>/`；prototype 票派 seed-prototype，verdict 写 Resolution；task 票 = 为解锁决策的体力活（取数、开权限、备环境）——agent 能代办则代办，否则给人精确步骤清单，Resolution 记录做了什么与产生的事实（凭据位置、新地址、数据规模），供下游票引用；HITL 票 agent 不得代替用户作答（正向）
* [x] 两条会话纪律成文：一会话只解决一张票（research 例外可并行）；图清 = frontier 空 + 雾区空 + 全票 closed → 建议转 brainstorm 收敛，不自动进 impl（边界）
* [x] 账本分离成文：票不进 `seed done`、不翻 PRD checkbox、不是 slice；`.arbor/maps/` 状态不构成第二套进度，图清即冻结（反向）
* [x] brainstorm 含分流线（大到一张 PRD 装不下或决策链还在雾里 → 先开图；一两次访谈能收敛 → 直接访谈）与收敛入口（图清后已拍决策读票不重问）两条（正向）
* [x] conventions.md 登记表新增 `seed-kit:wayfinder`；候选树 pytest 合同断言锁上述条款且全绿（正向）

### [x] S-003 seed map helper（new / status）

* [x] `seed map new <slug>` 脚手架 `.arbor/maps/<slug>/`（map.md 五节模板 + tickets/ 目录）；slug 已存在时拒绝并退出非零（正向/反向）
* [x] `seed map status <slug> [--json]` 从票 frontmatter 推导：open/closed 计数、frontier 列表（status: open 且 blocked-by 全 closed）；map.md 的散文节（如 Not yet specified）不进 --json 输出（正向）
* [x] 结构校验四项，有错退出非零并列出全部错误：票号唯一、blocked-by 引用存在的票、status ∈ {open, closed}、closed 票必有 `## Resolution` 节（反向）
* [x] `status` 只读：执行前后 map.md 与全部票文件内容不变（`new` 脚手架除外，map 子命令族无其他写操作）（边界）
* [x] 候选树 tests/test_seed.py 新增覆盖上述全部路径（含拒绝与校验失败分支），pytest 全绿（正向）

### [x] S-004 目录账本同步

* [x] 候选树 plugin.json、marketplace.json、根 README.md、DESIGN.md、`plugins/seed-kit/README.md`、`skills/references/conventions.md` 六处 skill 清单/数量与磁盘 `skills/` 目录一致（含 wayfinder 后的十个），过时数量词（"五个"/"六个"/"九个"）全部清除（正向）
* [x] 候选树 tests/test_prompt_contract.py 新增目录对账测试：walk `skills/*/`、`agents/`、`commands/` 与 conventions 登记表逐项一致（正向）
* [x] 对账测试可红：登记表人为删去任一条目时测试失败（红灯演示记录于候选树本 task 的 notes/）（反向）

### [x] S-005 eval 场景设计与静态校验（seed-kit-evals-v2 仓库）

* [x] 两个 experiment spec（value_ab）落盘：control = main 基线插件树（认证起始 HEAD）、treatment = 候选树；两臂 plugin_dir 与插件树 digest 进 run 指纹；实验期间两棵树内容冻结（正向）
* [x] prototype 价值场景三件套（story/setup/checks）：体验方向卡住的访谈型任务（planted gaps 仅作者/QA 可见），判 PRD 体验条目可证伪性与方向决策支撑，不以"调用了 seed-prototype"为 pass 主指标（正向）
* [x] wayfinder 价值场景三件套：大且雾需求（显式依赖链 D1→D2/D3→D4，QA 只答被问、"取决于上游"为合法回答），判未拍决策是否被烤死进 PRD 与提问顺序，不以"调用了 wayfinder"或"建了 .arbor/maps/"为 pass 主指标（正向）
* [x] 两实验各含三向可证伪 research 假设（更好/持平/更差均改变决策）与 not_measuring 声明（正向）
* [x] 全部场景过 `seed-evals check` 与 `check-red`；defaults：execution = deepseek-v4-flash（wanjie 中转已登记；unicom 凭据若已配可作备选）、judge = glm-5.3（需在 model-profiles.json judge 块新增登记）、trials ≥ 2（正向）
* [x] 两个新实验按该仓库惯例登记进 `scenarios/MANIFEST.md`（含存在理由；归档时同步移除）（正向）

### [x] S-006 跑实验与 CONCLUSION 结账（seed-kit-evals-v2 仓库）

* [x] `seed-evals value` 跑通两个实验，各产出 conclusion 枚举（improved/regressed/tradeoff/no_clear_difference/insufficient_evidence）与 cited_metric_ids（正向）
* [x] 两份 `experiments/<id>/CONCLUSION.md`：结论 + 由此建议的动作 + 模型指纹 + 置信度限制 + run-group id 与两臂插件 digest（供合并 gate 引用）（正向）
* [x] infra 类失败按归因纪律处理（indeterminate 重试 ≤2、不冒充行为结论）；无未结账实验残留（边界）

### [x] S-007 认证决策与合并 gate

* [x] CONCLUSION 含用户拍板记录：合并 / 回滚 / 修改后重试，三选一及理由（正向）
* [x] 拍板为合并：合并进 main 的被测面 diff 与认证 run 引用的候选树 digest 一致（不一致则认证作废，需重跑）（边界）
* [x] 拍板为不合并：候选分支归档保留，main 工作树与基线一致、零残留（反向）

## Out of Scope

* 引入 wizard / diagnosing-bugs / improve-codebase-architecture 等其他 mattpocock skill（用户确认）
* `seed map` 写操作子命令（close / ticket 等）——收票是 agent 写 Resolution 的语义动作，helper 保持只读（用户确认）
* seed_guard / hooks.json 扩展——票无 gate 语义（误关代价是补一张票，非伪造交付承诺），不加硬闸（用户确认）
* diagnosing-bugs 等未来候选的评估与场景设计（用户确认）
* prototype 独立 skill 壳（`/seed-kit:prototype`）——语义触发经 agent description 达成，不加用户触发入口（用户确认）
