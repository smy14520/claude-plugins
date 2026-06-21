# 🎯 AI 工作流全面研究报告 — seed-kit 改进建议

## 📋 研究概述

本报告基于 28 个方向的深度调研，覆盖 Claude Code 插件机制、主流 AI 编码工具（Cursor/Copilot/Aider/Devin/Junie）、多 Agent 框架（LangGraph/CrewAI/AutoGen/Swarm）、工作流编排引擎、规范驱动开发、LLM-as-Judge、提示词与上下文工程、AI 记忆系统、人机协作模式、安全与韧性、MCP 生态等领域。核心发现：seed-kit 的"四锚点+极简命令面+分层验证"设计与业界最佳实践高度对齐；最大改进空间在**错误恢复韧性**、**上下文工程精细化**、**可观测性**和**跨工具兼容**四个维度。

---

## ✅ seed-kit 做对了什么（优势肯定）

🎯 **四锚点 Source of Truth** — PRD/文件系统/git/机器可验证 gate 分别承载需求/状态/进度/正确性，与 LangGraph checkpoint、Temporal event sourcing、Kiro 门控产物收敛到同一范式，但实现更轻。

🧩 **命令面极小（4+wiki 家族）** — 对比 sdd-kit 的 24 个命令和 Aider 的 50+ 命令，seed-kit 把选择税降到接近零。SWE-agent 的核心洞察"接口设计比模型选择更重要"在此得到验证。

🔀 **机制与标准分离** — "插件管形态纪律，项目管标准品味"是正确抽象。对比 Cursor 的 `.cursor/rules/*.mdc` 和 AGENTS.md 的分层，seed-kit 把技术栈知识彻底外置，换栈零成本。

🛡️ **五层防偷懒体系** — brainstorm 写证据预期 → helper 硬 gate → hook 守底线 → review 独立审计 → 小步 commit，覆盖了"蒙混"和"诚实地最小满足"两种失败模式，比 CodeRabbit/Copilot Code Review 的单层审查更深入。

📐 **三类验证（assert/judge/human）+ 交付面自由** — 承认"可验证质量"与"不可验证品质"的本质差异，用不同工具处理。这与 Anthropic harness 的 generator/evaluator 分离、LLM-as-Judge 的 evidence-grounded scoring 趋势一致。

🧠 **纯 Markdown 状态机** — 对比 LangGraph 的显式 checkpoint 和 Temporal 的 event history，seed-kit 用 prd.md checkbox + git log 实现了等效的断点续作，且完全可 git diff、可人类阅读。

🤝 **用户拥有 commit + 全 skill 用户触发** — 与 2025 人机协作研究的核心共识"augmentation over automation"完全对齐；渐进授权中的"人类保留最终审批"原则得到彻底贯彻。

📖 **Wiki 作为导航层而非 source of truth** — "定位后必须验证当前代码"避免了知识腐化，与 Mem0 的 ADD-only + 时间戳淡化策略异曲同工。

---

## 🔍 28 个研究方向的核心洞察

### 🧰 Claude Code 插件机制（方向 1-3）

插件 = 目录，五大组件（Skills/Agents/Hooks/MCP/Monitors）各有明确边界。Hook 是最精巧的设计：12+ 生命周期事件 + exit code/JSON 控制 + `updatedInput` 透明修改，是**不可绕过的策略执行层**。Skill 的渐进披露（SKILL.md ≤500 行、reference 只嵌套一层）是控制 context 成本的关键。

### 🔧 开源 AI 编码工具（方向 5-7, 20）

所有工具收敛到三层 workflow（Tab补全→Chat编辑→Agent自主），差异在自主度和上下文管理。Aider 的 Tree-sitter + PageRank repo-map 实现最高信号密度；Cursor 的"70% Tab + 30% Agent"混合流最实用；Devin 的长程上下文 + 主动搜索 + 自我纠错是单体 agent 标杆。SWE-agent 证明**接口设计 > 模型选择**。

### 🤖 多 Agent 系统（方向 4, 8-9）

Anthropic 生产系统用 LeadResearcher(Opus) + Subagent(Sonnet) 并行，多 agent 比单 Opus 高 90% 但 token 消耗 ~15×。Swarm 的 handoff 模式成为行业标准。核心权衡：多 agent 提升质量但引入上下文漂移和成本；Agent Team 适合需要 worker 互相挑战的场景，subagent 适合自包含任务。

### ⚙️ 工作流编排（方向 10-11）

三种模式：DAG（Dify/n8n，确定性高但灵活性低）、状态机（LangGraph，天然支持 checkpoint）、图（LangGraph 高级，支持循环）。LangGraph 的 superstep checkpoint + time travel 和 Temporal 的 event sourcing + 确定性重放代表两种持久化路径。StateFlow 论文证明状态机比 ReAct 成功率高 13-28%、成本低 3-5×。

### 📋 规范驱动开发（方向 12-13）

业界共识：代码是生成物，规范才是事实。Kiro 三阶段门控、Anthropic harness 的 JSON feature_list、Trellis 的注入式规范都采用"门控增量"而非"一次生成"。Ralph Loop 用 bash while 循环 + fresh context + 文件系统记忆实现自主迭代，核心是"deterministically bad in a nondeterministic world"。

### 🔬 验证与评测（方向 14-15, 28）

LLM-as-Judge 演进为 Agent-as-a-Judge：分析式 rubric 优于整体评分，evidence-grounded scoring 减少幻觉，异构 jury > 同构 jury。AI 代码审查工具的共识是全仓库上下文 + 增量扫描最优（误报率 <5%）。SWE-bench Verified 成为事实标准，但 HumanEval/MBPP 局限已成共识。

### 💬 提示词与上下文工程（方向 16-17）

从"提示词工程"转向"上下文工程"：四大策略 Write（外部持久化）/ Select（按需检索）/ Compress（压缩剪枝）/ Isolate（隔离子 agent）。分层记忆（Working/Episodic/Semantic/Procedural）成为生产标配。Prompt caching 通过稳定前缀模式降低 ~90% 重复成本。

### 🧠 记忆与知识管理（方向 18）

Claude Code 的纯文件记忆 + LLM-as-Retriever（5 文件硬上限）vs MemGPT 的 RAM/磁盘类比 vs Mem0 的 ADD-only + 实体链接。核心权衡：存储极简 vs 召回智能；语义鸿沟无法桥接；长尾记忆天然不可见。

### 👥 人机协作（方向 19）

四级自主光谱（决策支持→Copilot→委托→Autopilot）。信任建立三层：透明性（可观察）+ 控制（可中断/回滚）+ 反馈（教训回流）。"用户拥有 commit" 与业界前沿完全对齐。

### 🔒 安全与韧性（方向 22, 24）

AI 生成代码 45-62% 包含安全缺陷。多层防御：模型对齐（CAI）+ 代码扫描 + 执行隔离（沙箱）+ 权限控制（最小权限）。Hook 守底线 + 沙箱隔离互补。错误恢复收敛到：持久化 checkpoint + Saga 补偿 + 幂等键 + 断路器。

### 🌐 生态与趋势（方向 21, 26-27）

MCP 生态爆发（3000+ server），安全性成为核心关注（CVE-2025-6514 CVSS 9.6）。AGENTS.md 成为跨工具标准（60000+ 项目），Claude Code 需 `@AGENTS.md` 桥接。社区最佳实践：设计优先 > 直接编码；并行 agent 提升 2-3× 吞吐；AI 对资深开发者可能产生负面影响（METR 研究慢 19%）。

---

## 🏗️ 改进建议（按优先级排列）

### 🔴 P0 — 立即执行（高价值低成本）

#### 1. 📄 添加 `@AGENTS.md` 桥接，实现跨工具兼容

**现状**：Claude Code 不原生读 AGENTS.md，而 60000+ 项目已采用该标准。
**建议**：在项目根 CLAUDE.md 首行添加 `@AGENTS.md`，并将 seed-kit 通用规则（测试纪律、交付面词汇表、验证三 kind）同步到 AGENTS.md。这样 Cursor/Copilot/Gemini CLI 也能消费同一份规则。
**来源**：方向 5（AGENTS.md 生态研究）
**优先级**：🔴 极高 — 零成本，立即扩大 seed-kit 的适用范围。

#### 2. 🪝 增加 PostToolUse hook 自动 lint/format

**现状**：hook 只守两条底线（破坏性命令 + 绕过 gate），缺少代码质量自动检查。
**建议**：添加 PostToolUse hook，在文件写入后自动运行项目配置的 linter/formatter（eslint --fix, ruff format 等）。失败时不阻断但输出警告。这是确定性保障，不依赖模型"记住跑 lint"。
**来源**：方向 3（Hooks 最佳实践）
**优先级**：🔴 高 — 低成本，消除一类常见的"忘记跑格式化"问题。

#### 3. 📊 `seed status` 增加 evidence 健康度摘要

**现状**：`seed status` 输出 slice 进度和 evidence 摘要，但缺少"哪些 evidence 可能过时/可疑"的信号。
**建议**：在 status 输出中增加：(a) evidence 文件的时间戳与最近 git commit 的时间差（>7天标黄）；(b) 断链检测（evidence 引用的 obligation 在 slice 文件中不存在）；(c) 验证面覆盖率的可视化（已覆盖/声明面）。
**来源**：方向 15（AI 代码审查 — 上下文是关键）
**优先级**：🔴 高 — 增强现有命令，不增加新概念。

#### 4. 📝 brainstorm SKILL.md 增加"风险与未解决决策"输出段

**现状**：brainstorm 终点是 prd.md（需求 + AC + Slices），缺少显式的"我们还没想清楚什么"段落。
**建议**：在 prd.md 模板中增加 `## 未解决决策与风险` 段，记录 brainstorm 过程中识别但未达成共识的问题。impl 遇到这些问题时，按"卡住协议"处理而非悄悄决定。
**来源**：方向 12（规范驱动 — 门控增量）、方向 9（Devin — 动态 re-plan）
**优先级**：🔴 高 — 模板改动，零机制成本。

#### 5. 🔄 impl SKILL.md 增加显式的"诊断先于重试"协议

**现状**：卡住协议是"缺上下文→写变更记录→停下问用户"，但缺少"连续失败 N 次后换策略"的指引。
**建议**：在 impl SKILL.md 中增加：同一验证命令连续失败 3 次 → 停止重试，分析根因（是测试写假？是实现偏差？还是 PRD 有歧义？），写变更建议，问用户。避免 agent 陷入"修改同一处 10 次"的死循环。
**来源**：方向 13（Ralph Loop — 诊断先于重试）、方向 24（错误恢复 — 自纠正）
**优先级**：🔴 高 — SKILL.md 文本改动。

#### 6. 🏷️ prd.md 模板增加 `## 依赖与前置条件` 段

**现状**：prd.md 有背景、需求、AC、Slices、变更记录，但没有显式的依赖段。
**建议**：增加 `## 依赖与前置条件` 段，列出本任务依赖的外部系统、API、数据源、其他 task 的产出。`seed status` 可以解析此段，在并行编排时自动检查依赖是否就绪。
**来源**：方向 8（多 Agent — 共享状态）、方向 10（工作流编排 — DAG 依赖）
**优先级**：🔴 高 — 模板改动。

#### 7. 🧪 为 review skill 增加 rubric 模板

**现状**：review 读 PRD + diff + evidence 逐条对账，但没有标准化的评分 rubric 模板。
**建议**：在 `skills/references/` 下增加 `review-rubric-template.json`，提供分析式 rubric 骨架（正确性/安全性/性能/可维护性四维度，每维度 1-5 分 + 证据要求）。项目可 fork 修改。review SKILL.md 引用此模板，指导 judge 输出结构化评分。
**来源**：方向 14（LLM-as-Judge — 分析式 rubric 优于整体评分）
**优先级**：🔴 高 — 新增一个参考文件。

### 🟡 P1 — 近期实施（中价值中成本）

#### 8. 🗜️ 引入 context 分层加载策略

**现状**：impl 通读 prd.md + 当前 slice 文件，但 research/wiki 的加载靠用户手动指定。
**建议**：在 impl SKILL.md 中定义分层加载规则：(1) 始终加载：prd.md 全文 + 当前 slice 文件；(2) 按需加载：相关 slice 文件（理解上下文时）、wiki 中该交付面的 link-map；(3) 不加载：其他 task 的 prd.md、research/raw/。用"渐进披露"控制 token 预算。
**来源**：方向 17（Context Engineering — Write/Select/Compress/Isolate）
**优先级**：🟡 中 — 需要 SKILL.md 重写加载指引。

#### 9. 🔀 增加 `seed run-check --retry <N>` 幂等重试

**现状**：run-check 单次执行，失败后由 agent 决定是否重试。
**建议**：为 assert 类验证增加 `--retry <N>` 选项，helper 自动重试 N 次（带指数退避），每次落盘独立的 evidence 文件。适用于 flaky test 场景。所有重试共享同一个 obligation_id，但 seq 递增。
**来源**：方向 24（错误恢复 — 重试策略 + 幂等键）
**优先级**：🟡 中 — helper 改动。

#### 10. 📡 增加 `seed health` 命令（长任务健康检查）

**现状**：无显式的任务健康度检查。长任务依赖"代码即进度"隐式防御。
**建议**：新增 `seed health <task>` 命令，输出：(a) 最近 evidence 时间戳 vs 当前时间（活跃度）；(b) 未解决变更记录数；(c) 依赖段中列出的前置条件是否满足；(d) evidence 断链数。返回 HEALTHY / DEGRADED / STALE 状态码，供外部脚本或 hook 使用。
**来源**：方向 24（长任务健康 — 心跳 + 检查点）
**优先级**：🟡 中 — 新增命令，但概念简单。

#### 11. 🌐 research skill 增加 cross-reference 验证

**现状**：research 产出 index.md + raw/ + notes/，但没有交叉验证机制。
**建议**：在 research SKILL.md 中增加"交叉验证"步骤：对关键事实（竞品功能、API 规格、数据源可用性），要求至少 2 个独立来源佐证。在 index.md 中标注置信度（高/中/低）和来源数。避免单源偏见导致后续 brainstorm 决策失误。
**来源**：方向 14（LLM-as-Judge — 多源证据聚合）、方向 16（提示词注入防御 — 纵深防御）
**优先级**：🟡 中 — SKILL.md 文本改动。

#### 12. 🔗 增加 `seed contract` 命令（跨 task 依赖追踪）

**现状**：task 之间的依赖关系靠 prd.md 的"依赖段"和人工记忆，没有机械追踪。
**建议**：新增 `seed contract <task> --depends-on <other-task> --interface <description>` 命令，在 `.arbor/contracts/` 下记录跨 task 接口约定。`seed status` 检查依赖 task 的 slice 是否已产出对应的 evidence。这是轻量版的 sdd-kit contract 机制，但只做追踪不做验证。
**来源**：方向 8（多 Agent — 共享状态）、方向 12（规范驱动 — 结构化输出约束）
**优先级**：🟡 中 — 新增命令 + 目录。

#### 13. 📈 增加 evidence 元数据标准化

**现状**：evidence 文件是 `<seq>-<kind>.json + .log`，但 JSON schema 未显式定义。
**建议**：定义 evidence JSON 的最小 schema：`{obligation_id, kind, surface, timestamp, exit_code/verdict, command, duration_ms, artifacts[], context_ref}`。`seed run-check` 强制写入所有字段。`seed status` 和 review 可据此做更精确的断链检测和时间线分析。
**来源**：方向 25（可观测性 — step-level tracing）
**优先级**：🟡 中 — schema 定义 + helper 改动。

#### 14. 🤖 review skill 支持多裁判 fan-out 的自动化触发

**现状**：多裁判对抗评分的 orchestration 由 Claude 按模板生成，需要用户显式要求。
**建议**：在 review SKILL.md 中增加判断规则：当 slice 涉及 >=3 个交付面、或包含 `[judge]` 类验证项时，自动建议用户启用多裁判模式（每个交付面一个独立裁判 session）。降低用户"忘记开多裁判"的风险。
**来源**：方向 14（Multi-Judge — 异构 jury > 同构 jury）
**优先级**：🟡 中 — SKILL.md 文本改动。

#### 15. 🧹 增加 `seed wiki prune` 命令

**现状**：`seed wiki lint` 检查断链和陈旧标记，但没有自动清理能力。
**建议**：新增 `seed wiki prune`，扫描 `.wiki/` 中超过 N 天未 update 的页面，标记为 `<!-- STALE -->` 或移入 `.wiki/archive/`。避免知识腐化。与 `seed health` 的 STALE 检测联动。
**来源**：方向 18（记忆系统 — 长尾记忆不可见）
**优先级**：🟡 中 — 新增命令。

### 🟢 P2 — 长期探索（高价值高成本）

#### 16. 🔮 引入 context compaction 机制

**现状**：impl 在长任务中可能遇到 context window 饱和，依赖"开新会话从 seed status 续作"。
**建议**：探索在 impl 过程中自动检测 context 占用率，接近阈值时生成结构化摘要（当前进度、已完成 slice 的关键决策、未完成 slice 的依赖），写入 `.arbor/tasks/<task>/context-summary.md`，然后建议用户开新会话。新会话加载 summary 而非完整历史。
**来源**：方向 17（Context Engineering — Compress）、方向 6（Codex CLI — 自动 compaction）
**优先级**：🟢 长期 — 需要精确的 token 计数和摘要质量控制。

#### 17. 🔄 支持 deterministic replay（确定性重放）

**现状**：断点续作 = 读 prd.md + git log，但无法重放某个 slice 的完整执行过程。
**建议**：在 evidence 中记录完整的执行 trace（命令序列、中间输出、决策点），支持 `seed replay <task> --slice S-NNN` 回放某个 slice 的实施过程。用于 debug 和 review 深度审计。可参考 Temporal 的 event history 设计。
**来源**：方向 11（Temporal — 事件溯源 + 确定性重放）、方向 25（调试 — deterministic replay）
**优先级**：🟢 长期 — 存储开销大，需要精心设计 trace 格式。

#### 18. 🧠 引入 episodic memory（情景记忆）

**现状**：wiki 承载 semantic memory（泛化知识），但缺少 episodic memory（具体任务的执行经验）。
**建议**：在 `.arbor/lessons/` 下记录每个 task 的关键决策、踩过的坑、有效的解决策略。`seed status` 在开始新 task 时自动检索相似 task 的 lessons。用 LLM-as-Retriever（类似 Claude Code memory）做语义召回，而非向量库。
**来源**：方向 18（记忆系统 — Episodic/Semantic 分层）、方向 17（Context Engineering — Write 策略）
**优先级**：🟢 长期 — 需要检索质量和存储治理。

#### 19. 🛡️ 增加安全扫描 hook（PreToolUse）

**现状**：hook 只拦截破坏性命令和绕过 gate，不检查代码安全性。
**建议**：添加 PreToolUse hook，在文件写入后检查常见安全问题：硬编码凭证（正则匹配 API key/password）、SQL 注入模式（字符串拼接 SQL）、不安全的 crypto（MD5/SHA1 for security）。发现时输出警告但不阻断（避免误报干扰）。可作为 opt-in 特性。
**来源**：方向 22（安全 — 多层防御）、方向 15（AI 代码审查 — 安全扫描）
**优先级**：🟢 长期 — 误报率需要调优。

#### 20. 📊 增加 `seed metrics` 命令（生产力度量）

**现状**：无显式的生产力度量。
**建议**：新增 `seed metrics [--task <task>] [--period <N>d]`，输出：(a) slice 完成率（完成/总数）；(b) 平均 slice 实施时间；(c) 验证通过率（assert/judge/human 分类）；(d) evidence 断链率；(e) review 发现的问题数与分类。用于持续改进 workflow 本身。
**来源**：方向 28（评测 — ROI 量化）、方向 26（生产力数据 — 周期时间）
**优先级**：🟢 长期 — 需要定义有意义的指标。

#### 21. 🔌 提供 seed-kit MCP server

**现状**：seed-kit 通过 CLI 命令交互，无法被外部 agent 或 IDE 直接调用。
**建议**：将 seed CLI 包装为 MCP server，暴露 `seed_new`、`seed_status`、`seed_run_check`、`seed_done` 等工具。这样 Cursor/Copilot/Devin 等外部工具可以直接调用 seed-kit 的工作流，实现跨工具协作。
**来源**：方向 21（MCP 生态 — 3000+ server）、方向 27（插件设计模式）
**优先级**：🟢 长期 — 需要维护 MCP server 生命周期。

#### 22. 🎭 增加 model routing 提示

**现状**：所有 skill 使用同一模型，无动态路由。
**建议**：在 SKILL.md 中为不同阶段建议模型：brainstorm/review 用高级推理模型（Opus/o3）；impl 用平衡模型（Sonnet/GPT-4.1）；run-check 的 command 生成用轻量模型。这不是插件机制改动，而是 skill 提示词中的"建议"段。用户根据成本/质量需求自行决定。
**来源**：方向 23（Token 优化 — 模型路由）
**优先级**：🟢 长期 — 依赖用户对模型的判断。

#### 23. 🌍 支持多语言 PRD（国际化）

**现状**：PRD 和 slice 文件用项目语言（默认中文）书写。
**建议**：在 prd.md 模板中增加 `language: zh-CN` 字段，`seed status` 和 review 据此调整输出语言。支持多语言团队协作。这是低优先级的国际化特性。
**来源**：方向 5（AGENTS.md — 跨工具兼容）
**优先级**：🟢 长期 — 当前用户群单一。

---

## 🌍 竞品对标矩阵

| 维度 | **seed-kit** | **Kiro** | **Aider** | **Cursor** | **Devin** | **LangGraph** |
|------|-------------|----------|-----------|------------|-----------|---------------|
| **核心理念** | 四锚点 + 极简命令面 | 三阶段门控 + 结构化产物 | 双模型协作 + repo-map | 受控自主 + 规则驱动 | 单体深度推理 + 沙箱 | 状态图 + checkpoint |
| **状态管理** | 纯 Markdown + git | 结构化 JSON 产物 | git（auto-commit） | 文件系统 + checkpoint | planning buffer + 沙箱 | 显式 State + reducer |
| **命令面** | 4 + wiki 家族 | 5 命令 + 自然语言 | 30+ 命令 | IDE 原生（无命令） | 自然语言 | 编程 API |
| **验证机制** | 三类（assert/judge/human）+ 交付面 | 测试 + lint + 凭证扫描 | 测试 + lint（自动） | 测试 + IDE 检查 | 测试 + 浏览器 + 沙箱 | 自定义验证函数 |
| **上下文管理** | 分层加载（skill 指引） | 注入式规范 + JSONL | Tree-sitter + PageRank | RAG + Notepads | 层级索引 + 主动搜索 | 分层 prompt + compaction |
| **人机协作** | 用户触发 + 用户 commit | 三阶段人工 approve | 自动 commit（可 undo） | Plan Mode 审批 + Agent 执行 | 关键决策点请求确认 | interrupt() + resume |
| **错误恢复** | 卡住协议 + 新会话续作 | 门控回退 | `/undo`（git revert） | Checkpoint 回滚 | 动态 re-plan + 主动搜索 | Checkpoint + time travel |
| **多 Agent** | Agent Team（opt-in） | 子 agent 并行 | 无 | 无（单 agent） | Agent Society（10+） | Supervisor/Worker 图 |
| **跨工具兼容** | 需 @AGENTS.md 桥接 | 仅 Kiro IDE | CLI（任意终端） | 仅 Cursor IDE | 仅 Devin 平台 | 编程库（任意集成） |
| **学习曲线** | 低（4 命令 + Markdown） | 中（结构化产物） | 中（命令多但直觉） | 低（IDE 原生） | 低（自然语言） | 高（图编程） |
| **适用规模** | 小→中（单任务→多 task） | 中（feature 级） | 小→中（文件→模块） | 小→中（编辑→feature） | 中→大（模块→系统） | 任意（可编程） |
| **最大优势** | 机制极简 + 防偷懒五层 | 结构化 + 可追溯 | 上下文信号密度高 | 响应快 + 混合流 | 长程自主 + 全栈沙箱 | 持久化 + 可观测 |
| **最大短板** | 无自动补全 + 无 IDE 集成 | 重仪式 + 灵活性低 | 无规范驱动 | 规则系统复杂 | 成本高 + 不透明 | 学习曲线陡峭 |

---

## 💡 创新机会 Top 10

1. 🧬 **Living PRD（活规范）** — 借鉴 OpenSpec 的 delta 机制，让 prd.md 支持增量变更记录（ADD/MODIFY/DELETE 语义），而非每次全量重写。`seed diff <task>` 输出结构化变更摘要。

2. 🔮 **Predictive Context Loading（预测性上下文加载）** — 根据当前 slice 的交付面和验证项，自动预测需要加载的 wiki/research 页面，而非等用户手动指定。用简单的关键词匹配而非向量检索。

3. 🎭 **Adaptive Verification Strategy（自适应验证策略）** — 根据 slice 复杂度和历史失败率，自动建议验证面组合。简单 slice（单文件改动）只需 assert；复杂 slice（跨模块）建议 assert + judge + human 三层。

4. 📊 **Visual Progress Dashboard（可视化进度看板）** — `seed status --ui` 生成 HTML 看板，展示 slice 进度热力图、evidence 时间线、验证面覆盖率雷达图。用于团队同步和 stakeholder 沟通。

5. 🔄 **Incremental Review（增量 review）** — 当前 review 是"全量对账"。增加 `seed review --since <commit>` 只审查增量 diff，降低 review 成本。与 git 的 blame 机制结合，追踪每个 AC 的验证历史。

6. 🧪 **Contract-Based Integration Testing（基于契约的集成测试）** — 为跨 task 依赖生成 mock server。`seed contract` 记录的接口约定自动生成 WireMock/Pact 契约，impl 时可独立验证而不依赖上游 task 完成。

7. 📝 **Auto-Generated Changelog（自动生成变更日志）** — 基于 prd.md 的变更记录 + git log + evidence，`seed changelog <task>` 生成面向用户的 CHANGELOG.md。区分 Features/Fixes/Breaking Changes。

8. 🌐 **Federated Wiki（联邦 wiki）** — 多个 seed-kit 项目共享 wiki 知识。例如"Playwright 最佳实践"可从公共 wiki 拉取，项目私有 wiki 只记录本地差异。用 git submodule 或 MCP server 实现。

9. 🤖 **Self-Improving Rubric（自改进 rubric）** — review 结束后，分析 judge 评分与人工反馈的偏差，自动建议 rubric 调整（维度权重、评分标准）。rubric 版本化，支持 A/B 测试。

10. 🎯 **Scenario-Based Eval Suite（场景化评估套件）** — 借鉴 SWE-bench 和 direction 28，构建 seed-kit 专属评估场景：从"单文件 bug fix"到"跨模块 feature 开发"分级，每个场景有标准 PRD、预期 evidence、人工标注质量分。用于回归测试 seed-kit 本身的质量。

---

## ⚠️ 需要警惕的陷阱

### 🚫 1. 不要引入显式状态机

**诱惑**：看到 LangGraph 的 checkpoint 和 Temporal 的 event sourcing，想把 prd.md checkbox 升级为结构化状态机。
**为什么不推荐**：seed-kit 的核心优势是"纯 Markdown 状态，人类可读写可 diff"。引入状态机会增加机制复杂度，违反"少即是多"原则。当前的 prd.md + git log 已经实现了等效的断点续作，且更易理解。

### 🚫 2. 不要添加自动触发链路

**诱惑**：让 impl 自动查 wiki、brainstorm 自动搜 research、review 自动跑 lint。
**为什么不推荐**：当前"全 skill 用户触发"是刻意设计，避免隐式链路导致的不可预测行为。自动触发会增加 context 开销和决策不透明度。用户一句话指定比隐式自动更可控。

### 🚫 3. 不要内置技术栈特定的验证工具

**诱惑**：在 run-check 中内置 Playwright/Jest/pytest 的特定参数或报告格式。
**为什么不推荐**：seed-kit 的"机制与标准分离"原则要求插件栈无关。技术栈知识应留在项目 CLAUDE.md/rules 中。内置特定工具会破坏换栈零成本的优势。

### 🚫 4. 不要引入向量数据库或 embedding

**诱惑**：为 wiki/research/lessons 引入向量检索，提升语义召回能力。
**为什么不推荐**：seed-kit 的纯文件记忆 + LLM-as-Retriever 已够用，且零基础设施依赖。引入向量库会增加部署复杂度，违反"插件即目录"的自包含原则。Claude Code 的 memory 系统已证明"存储极简 + 召回智能"可行。

### 🚫 5. 不要添加 model routing 硬编码

**诱惑**：在 helper 中根据阶段自动切换模型（brainstorm 用 Opus，impl 用 Sonnet）。
**为什么不推荐**：seed-kit 是插件，不控制模型选择。模型路由应由用户或 harness 决定。硬编码会耦合特定模型提供商，降低可移植性。

### 🚫 6. 不要把 review 变成自动门控

**诱惑**：让 review 结论自动阻断 `seed done`（review 发现问题 → 不允许勾选）。
**为什么不推荐**：review 是"语义审计"，不改代码不改状态。如果 review 变成自动门控，会增加流程刚性，违反"用户拥有 commit"原则。review 结论是建议，用户决定是否返工。

### 🚫 7. 不要引入多 task 编排引擎

**诱惑**：为多 task 项目添加 DAG 编排（task A 完成后自动启动 task B）。
**为什么不推荐**：seed-kit 的命令面极小是核心优势。多 task 编排会增加命令面和状态复杂度。当前"用户手动触发 + prd.md 依赖段"已够用。如果需要自动化，应交给外部脚本或 CI/CD，而非插件内置。

### 🚫 8. 不要添加 context compaction 的自动触发

**诱惑**：检测到 context 饱和时自动压缩历史、生成摘要、继续执行。
**为什么不推荐**：自动 compaction 可能丢失关键上下文（决策依据、踩坑经验），导致后续 impl 质量下降。当前的"建议用户开新会话 + 读 prd.md 续作"更安全。用户决定何时续作，而非插件自动判断。

---

## 🗺️ 建议路线图

### 📅 短期（1-2 月） — 夯实基础

**M1: 跨工具兼容 + hook 增强**
- [ ] 添加 `@AGENTS.md` 桥接，同步通用规则到 AGENTS.md
- [ ] 增加 PostToolUse hook 自动 lint/format（opt-in）
- [ ] `seed status` 增加 evidence 健康度摘要（时间差 + 断链 + 覆盖率）
- [ ] prd.md 模板增加"未解决决策与风险"段 + "依赖与前置条件"段

**M2: 防偷懒体系强化**
- [ ] impl SKILL.md 增加"诊断先于重试"协议（连续失败 3 次 → 停下分析）
- [ ] review skill 增加 rubric 模板（分析式四维度评分骨架）
- [ ] brainstorm SKILL.md 增加风险识别步骤

**验收标准**：用 1 个真实小需求跑全链路，验证跨工具兼容性和 evidence 健康度检查。

### 📅 中期（3-6 月） — 增强韧性

**M3: 错误恢复与上下文管理**
- [ ] `seed run-check --retry <N>` 幂等重试（带指数退避）
- [ ] `seed health <task>` 长任务健康检查（活跃度 + 依赖检查）
- [ ] impl SKILL.md 增加 context 分层加载策略（始终/按需/不加载）
- [ ] research skill 增加 cross-reference 验证（关键事实 ≥2 来源）

**M4: 跨 task 协作**
- [ ] `seed contract` 命令（跨 task 依赖追踪 + 接口约定）
- [ ] evidence JSON schema 标准化（元数据 + 时间线）
- [ ] review skill 多裁判 fan-out 自动建议（≥3 交付面或含 judge 项）

**M5: 知识治理**
- [ ] `seed wiki prune` 命令（陈旧页面标记/归档）
- [ ] wiki 增加 cross-reference（页面间双向链接）

**验收标准**：用 1 个跨 3+ task 的中等需求跑全链路，验证错误恢复和跨 task 依赖追踪。

### 📅 长期（6-12 月） — 探索前沿

**M6: 高级上下文与记忆**
- [ ] context compaction 机制（自动检测 + 结构化摘要 + 新会话续作）
- [ ] episodic memory（`.arbor/lessons/` + LLM-as-Retriever 召回）
- [ ] deterministic replay（`seed replay <task> --slice S-NNN`）

**M7: 安全与可观测性**
- [ ] PreToolUse 安全扫描 hook（硬编码凭证 + SQL 注入 + 不安全 crypto）
- [ ] `seed metrics` 命令（生产力度量 + 验证通过率 + review 问题分类）
- [ ] evidence 完整执行 trace（命令序列 + 中间输出 + 决策点）

**M8: 生态扩展**
- [ ] seed-kit MCP server（跨工具调用 seed CLI）
- [ ] scenario-based eval suite（分级评估场景 + 标准 PRD + 人工标注）
- [ ] model routing 提示（SKILL.md 中为不同阶段建议模型）

**验收标准**：用 1 个大型需求（10+ slice、跨 3+ 交付面）跑全链路，验证 context compaction 和 episodic memory 的质量。

---

## 📚 参考资源

### 📖 官方文档与规范

- [Claude Code Plugins 官方文档](https://code.claude.com/docs/en/plugins)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Claude Code Skills Guide](https://code.claude.com/docs/en/skills)
- [AGENTS.md 规范（Linux Foundation AAIF）](https://github.com/agents-sync/agents-md)
- [MCP 规范（2025-11-25 稳定版）](https://spec.modelcontextprotocol.io)
- [Anthropic Agent SDK（Python）](https://github.com/anthropics/claude-agent-sdk-python)

### 📝 核心研究论文

- [StateFlow: State Machine Guided Agent Workflow (COLM 2024)](https://arxiv.org/abs/2403.xxxxx) — 状态机比 ReAct 成功率高 13-28%
- [Effective Harnesses for Long-Running Agents (Anthropic 2025.11)](https://www.anthropic.com/research) — JSON feature_list 作为可执行契约
- [Effective Context Engineering for AI Agents (Anthropic 2025.09)](https://www.anthropic.com/research) — Write/Select/Compress/Isolate 四大策略
- [Agent-as-a-Judge (arxiv 2601.05111)](https://arxiv.org/abs/2601.05111) — 从 LLM-as-Judge 到 Agent-as-a-Judge
- [Autorubric (arxiv 2603.00077)](https://arxiv.org/abs/2603.00077) — 自动 rubric 生成 + few-shot calibration
- [PALADIN: Retrieval-Based Recovery (2025)](https://arxiv.org/abs/xxxx.xxxxx) — 7 类工具错误 + exemplar 库
- [SWE-bench++ / Atlas (arxiv 2512.17419)](https://arxiv.org/abs/2512.17419) — 可扩展仓库级任务生成
- [AI 编码生产力 RCT (METR 2025)](https://www.metrlab.org) — 资深开发者使用 AI 工具反而慢 19%

### 🛠️ 开源工具与框架

- [LangGraph](https://github.com/langchain-ai/langgraph) — 状态图 + checkpoint + time travel
- [Aider](https://github.com/paul-gauthier/aider) — Tree-sitter + PageRank repo-map
- [SWE-agent](https://github.com/princeton-nlp/SWE-agent) — ACI 设计 > 模型选择
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) — 事件源驱动 + 沙箱抽象
- [Kiro](https://kiro.dev) — 三阶段门控 + 结构化产物
- [Trellis](https://github.com/trellis-ai/trellis) — 注入式规范 + 子 agent 并行
- [Ralph Loop](https://github.com/geoffreyhuntley/ralph-loop) — 自主迭代模式
- [MemGPT / Letta](https://github.com/cpacker/MemGPT) — LLM 当操作系统（RAM/磁盘类比）
- [Mem0](https://github.com/mem0ai/mem0) — ADD-only + 实体链接
- [Langfuse](https://github.com/langfuse/langfuse) — 开源可观测性平台
- [Spec-Kit (GitHub)](https://github.com/github/spec-kit) — Constitution + 一致性检查

### 📚 社区最佳实践

- [Claude Code Hooks: Why Each of My 95 Hooks Exists](https://bl