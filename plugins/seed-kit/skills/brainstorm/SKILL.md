---
name: brainstorm
description: "访谈式把模糊想法收敛成可执行的 PRD（.arbor/tasks/<task>/prd.md：可证伪 AC + 有序 slice）。"
---
# Brainstorm — 需求收敛访谈

> 调用名：`seed-kit:brainstorm`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

把一个模糊想法收敛成可执行的 PRD。从零开始的项目要引导用户做关键决策（选型、形态、范围）；已有项目要先读代码、CLAUDE.md 理解现状与既有模式，只对**直接影响本任务**的问题提改进，并问边界与接缝。

## 开图还是直接访谈

入场先判断形态：大到一张 PRD 装不下，或决策链还在雾里（决策互相咬、先答哪个决定后面问什么）→ 建议开图，用户确认后当场进入 wayfinder（不要求重新点名），把决策链拆成票跨会话一张张拍，图清后再回来收敛；一两次访谈能收敛的 → 直接进入访谈循环。图清后来收敛的：已拍的决策读票的 `## Resolution`，不重问——访谈只问还没拍的。

## 访谈循环

持续追问，直到每个会影响实现结果的隐含决策都被拍板，没有重要假设被沉默地默认带过：

- 沿决策树每个分支走到能写出**可证伪验收**的叶子，按轮次推进：每轮只问前置已定的问题（frontier），依赖还没拍板的问题留到下一轮，不提前问。还有未拍板的隐含决策时，不产出 PRD。
- 对有用户可感面的产品（UI/CLI/文案/API DX），了解期望的体验方向：参考产品、设计语言、"感觉像 X"、明确不要的样子。用参考而非清单——参考传递丰富先验，让 impl 发挥判断力。这些自然写入 Goal 和验收条目中，不独立成段。
- **形容词吵不出结果的设计问题派原型**：访谈中出现"跑起来才知道"的分叉（两种交互哪种顺、这个状态模型手感对不对、这该长什么样）时，派 `seed-prototype` agent 造一次性原型让用户直接玩——产物落 `.arbor/prototypes/<slug>/`（自包含单 HTML，不进交付），用户玩出的 verdict（问题 + 拍板答案）折进访谈结论，继续推进而不是停在口头争论。
- **提问通道看场景**：人在环上（真实交互）用 **AskUserQuestion 工具**——`questions` 只放一条（一次一题），2–4 个选项，推荐项置首、label 带"(推荐)"，取舍写进各选项 description；开放题也走选项（用户可选 Other 自由输入）。**脚本化 / 无交互驱动**（如自动化测试 harness）改用**纯文本散文一次一题**——不要调用 AskUserQuestion（驱动端无法回答菜单，会卡死）。
- 找事实是你的活，不是用户的：凡能从仓库、文档或官方源查到的事实，先自行查证再问，不要把用户当数据库。必要时查看与需求直接相关的近期提交，确认正在演化的接口、边界或约定。耗时查证可派 sub-agent 后台进行，不阻塞本轮其余问题——只有依赖它结论的问题等它回来。
- 只有存在会显著影响范围、接口、成本或后续 slice 的真实分叉时，给 2–3 个可行方向与取舍，推荐项置首。
- 收敛前追问一次隐性期望：用户默认成立但没写出口的期望里，哪些值得写成可证伪条目？值得守的落条目，不值得的显式进 Out of Scope——让"不守"也是决定而非遗漏。**排除是用户的决策**：任何你认为"不值得做"的点，写进 Out of Scope 前必须先问过用户（走本 skill 的提问通道），不能单方拍板。项目标准层（CLAUDE.md / DESIGN.md / .claude/rules）已声明的质量基线，与本任务相关的转译成本任务条目。维度按项目语境判断，不套通用清单。
- **易过期事实**（版本号、发布日期、最新 API、依赖兼容性、弃用状态）——推荐前先通过 WebSearch/WebFetch 查官方源（releases、官方文档、changelog）的**当前值**，不靠回忆。这是"不主动搜索"的唯一例外：只查单个易过期事实，不开 research 主题。进 PRD 时这类事实带 `查证于 <日期>（<来源>）` 标注，例如 `Laravel 13.x（查证于 2026-06-15，laravel.com/releases）`。架构概念、语法、原理等非易过期事实照常靠记忆。
- 入场时跑 `seed wiki index --json` 加载项目记忆——全量索引（title + description + type + area），轻量无负担。访谈过程中扫描索引，自行读取相关的 decision / module / cross_cut 页作为背景上下文。

## 产出 PRD

用户确认收敛结果后：

1. `seed new <task>` 创建任务目录。
2. 按模板填写 `prd.md`（Goal + Design + Acceptance Criteria + Out of Scope）：
   - **Goal**：一段话概述——这是什么、为什么做；痛点句删掉方案词后必须仍成立（Problem 不依赖解）。有可感面时，期望的体验方向（参考产品、设计语言、"感觉像 X"）自然融入。
   - **Design**：整体层——状态空间（实体与状态迁移全表，枚举出的状态都有迁移可达）、跨片联动（机制相交处的行为写在这里，slice 条目引用本节）、接口契约（slice 间消费/产出）。轻任务写一行"无——轻任务（用户确认）"跳过。
   - **Acceptance Criteria**：有序 slice（`### [ ] S-NNN 标题`），每个 slice 下用 `* [ ]` 写验收条目。一个 `* [ ]` 一个测试用例——正向一条、反向一条、边界一条。技术决策融入相关条目，不独立成段。
   - **wiki 知识区分**：精确位置（文件/函数/插入点）直接写进验收条目——这是 task 特定的，没有复利价值。模式/原理/陷阱（"为什么这么设计""这个坑怎么避"）用 `[[../.wiki/页面路径]]` 引用——让 impl 自己去读原文，同一个原理不存两份。
   - **Out of Scope**：明确不做什么。每条排除都必须是用户确认过的决定——访谈中问过的直接落盘，没问过的回提问通道补问一次；写入时末尾带（用户确认）标注（`seed status` 拒绝无标注条目）。
   - 所有 slice 内容直接写在 prd.md 的 `### [ ] S-NNN` heading 下，无单独 slice 文件。
3. PRD 落盘后做一次 inline self-review：清除 TBD/TODO、占位符和模糊语句；核对 Goal、Design、Acceptance Criteria、Out of Scope 是否一致，task 是否过大到应拆成独立 task，以及每条 AC 是否只有一种可执行解释。发现问题直接修当前 PRD，不新增 artifact 或 stage。
4. 自审并修正后，再运行 `seed status <task>` 校验结构（有结构错误必须修复并重跑）。

slice 拆分由你推荐、用户确认。**先呈方案再落盘**：拆片前先列出本任务会触及的全部层（e.g. schema / API / UI / tests——层随项目栈现场点名，如 CLI 的参数解析/核心逻辑/输出、游戏的玩法/渲染/资源）；然后把切片方案呈给用户——每片一句话，说它让哪个**用户视角的端到端行为**可用（不是分层实现清单）；用户确认后再写 PRD。不强制最小切片，也不要为了显得完整而拆假边界。

**每个 slice 落地时必须单独绿**：gate 独立通过，验收只判自己拥有的东西。切法由改动形状决定——

- **切片规则**：*"Each slice cuts a narrow but COMPLETE path through every layer — vertical, NOT a horizontal slice of one layer. A completed slice is demoable or verifiable on its own."* 每片穿过上面点名的所有层；"可验证"指能演示这一片的行为——测试测的正是这条行为才算数。
- **S-001 是 tracer bullet**：一条最薄的端到端路径，穿过上面点名的全部层，每层只做这条路径需要的部分——不必覆盖 Design 的全部承诺，先让整条路走得通、能演示；后续 slice 各自增厚一个端到端能力。常见偏移：肥大的地基片（一层做全再做下一层）。
- 机械大改（一刀波及全仓的单一变更，如统一改名）**按 expand–contract 切**：expand（新形态加在旧旁，旧的不动）→ migrate（按模块分批迁移调用点，每批一个 slice）→ contract（全迁完删旧）。每一步仍然单独绿。

**后到的 slice 认领交界**：前序 slice 交付的操作，在本 slice 引入的新机制/新维度下的行为，成为本 slice 拥有的一部分、归它验收——逐个走一遍，写成条目或（用户确认）排除；无主就是漏。

slice 的尺寸判据：一个新鲜 context window 装得下；装不下说明它是 task 不是 slice。大项目按域拆成多个 task（各自一份 PRD、独立 gate）逐个收敛；task 间有真依赖时建议去 wayfinder 拍序列（动作定义见 wayfinder「图清与交棒」），用户确认后当场进入。

## 修改既有 PRD

需求变化时直接编辑 prd.md（不动 checkbox）。

## 停止

PRD 写好并通过 `seed status` 校验后：
- **project-scoped 决策**——以后做其他 task 的人也需要知道的——落 `.arbor/.wiki/decision/` 页；决策融入验收条目的部分已在 PRD 里，不重复。
- **新模块或模块边界变化**落 `.arbor/.wiki/module/` 页。
- 跑 `seed wiki index --write` 刷新索引和日志。

PRD 通过 `seed status` 校验后，**自动派 `seed-prd-review`**（独立上下文；只传审查任务，不传你的访谈推理与预设结论）——PRD 独立审查是默认收尾工序，不待用户点名。发现 serious gap 时：修复 PRD → 重跑 `seed status` → 重审，直到 clean，结论摘要交给用户。impl 是重操作——由用户显式点名，不自动进入。
