---
name: research
description: "Bounded exploration of a topic before committing to a spec/design. Produces `.claude/research/<topic>/` with raw materials, refined notes, and a `findings.md` summarizing discoveries + open questions + wiki-ingest candidates. Does NOT make design decisions (spec skill's job) and does NOT auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — 有边界的信息探索

在 `.claude/research/<topic>/` 下产出聚焦的探索记录。将原始收集与提炼整理分离为不同步骤。完成后将控制权交还用户，不自动推进。

## 在四阶段工作流中的定位

```
[research] → spec → task → impl
     ↓
     └─── 用户选择性摄入 wiki（仅用户触发）
```

本 skill 仅负责**探索**阶段。它：

- 收集原始素材（代码库阅读、文档、URL、用户提供的材料）
- 提炼为简短的精炼笔记
- 抛出 spec 阶段必须解决的开放问题
- **不做**架构选择，不敲定设计方案
- **不自动**触发 `spec`

Research 的产出是**临时上下文**。只有用户明确提升的条目才会成为 wiki 知识。

## 五个原语

根据用户意图匹配对应原语；完整流程见 [references/workflow.md](references/workflow.md)。

### 🎯 Scope — 定义问题边界 + 锚定意图

触发词："调研 X"、"研究一下 X"、"想做 X 先探索"。

流程（详见 `references/workflow#scope`）：

1. 用一句话复述研究问题
2. 列出范围内事项（2-8 项）
3. 列出明确排除的事项（防止范围膨胀）
4. 填写**意图锚定**：
   - Decision type：选型 / 估工 / 理解现状 / 评估可行性
   - Success criteria：什么算"有用的发现"（1-3 条具体标准）
   - Downstream：spec-name / 直接回答 / wiki 摄取
5. 使用模板 [assets/templates/question.md](assets/templates/question.md) 生成 `question.md`

### 📥 Collect — 收集原始素材

触发词："收集 X 的资料"、"看一下代码里 X 怎么做的"，或用户粘贴文档/URL。

流程：

1. 接收原始输入（粘贴的文档、URL、截图、代码片段）→ `raw/`
2. 扫描代码库中相关入口 → 提取最小化引用，保存为 `raw/codebase-<area>.md`
3. **用户提供的 URL = 强制获取**：穷尽工具阶梯，需要登录则暂停请求用户协助，不可静默跳过。按 [references/data-collection.md](references/data-collection.md) 中的信号驱动策略执行。
4. 研究过程中发现的 URL：按意图锚定的 success criteria 判断是否追踪。
5. **此时不做研究性提炼**。允许对原始素材做低损清洗和格式规范化，但不得改变来源事实、不得合并判断、不得产出设计结论。
   对 HTML / API 文档 / 网页材料，`raw/` 中保存的是 cleaned source note：
   - 删除导航栏、页脚、脚本、样式、广告、cookie banner、重复菜单等展示噪音
   - 保留接口路径、HTTP 方法、参数、headers、认证方式、请求/响应示例、错误码、状态码、分页、rate limit、retry 语义、版本信息、注意事项
   - 将表格、列表、代码块转换为 Markdown
   - 记录来源 URL、抓取时间、使用的工具
   - 不得把多个来源综合成结论；综合分析只允许出现在 `refined/`。

### 🔍 Refine — 提炼为聚焦笔记

触发词："整理一下"、"把收集到的提炼一下"。

流程：

1. 针对每个独立发现，写一篇短文 `refined/<topic>.md`（不超过 120 行）
2. 每篇精炼笔记包含：发现了什么 / 来源在哪里 / 为什么重要（关联意图锚定）/ 引出了什么开放问题
3. 多个来源说法冲突时使用 `## Conflicting evidence` 段记录，不在 research 阶段裁定
4. 保留未贡献到任何精炼笔记的 raw 文件，不删除（在 findings.md 中标注 unused）
5. 应用模板 [assets/templates/finding-note.md](assets/templates/finding-note.md)

### ✅ Check — 完整性检查（Refine → Propose 之间的门控）

提炼完成后、提议之前必须通过：

1. 意图锚定的每条 success criteria 是否都有至少一条 refined 笔记回应？
2. question.md 中的子问题是否都被涉及？
3. 是否发现了范围需要调整的信号？

未通过 → 回到 Collect 补充或执行 re-scope。

### 📐 Re-scope — 修订范围（可选）

当提炼或完整性检查揭示 question.md 需要调整时：

1. 不删除旧内容，在 `## Scope history` 表中追加变更记录
2. 更新 In scope / Out of scope / Intent anchor
3. 已有文件保留，标注哪些是旧范围的产出

### 📤 Propose — 呈现发现 + 摄入建议

触发词："总结一下 research"、"research 完了"、"可以结束研究了"。

流程：

1. 使用模板 [assets/templates/findings.md](assets/templates/findings.md) 生成 `findings.md`
2. 列出关键发现（直接影响决策，链接到 `refined/` 笔记）
3. 列出背景发现（提供上下文但不直接影响决策）
4. 列出开放问题（供 spec 解决）
5. 列出 **wiki 摄入候选**：每个附一句理由（不做 wiki 类型分类）—— 不自动执行摄入
6. 输出收尾摘要；**不调用** spec skill

## 目录结构

```
.claude/research/<topic>/
├── question.md                  # 范围 + 排除项 + 意图锚定 + 范围变更记录
├── raw/                         # 原始收集，低损清洗和格式规范化（不删除）
│   ├── codebase-<area>.md       # 来自代码的引用，含 file:line 引用
│   ├── ext-<source>.md          # 外部材料摘要
│   ├── ext-<source>-failed.md   # 获取失败的外部来源
│   └── user-input-YYYY-MM-DD.md # 用户粘贴的材料
├── refined/                     # 提炼后的发现，每个话题一个文件
│   ├── <finding-1>.md
│   └── <finding-2>.md
└── findings.md                  # 总结 + 开放问题 + 摄入候选
```

`<topic>` 使用 kebab-case 命名，按话题命名（不使用日期）。示例：`.claude/research/xhs-customer-webhook/`。

## 核心规则

1. **意图锚定是一等公民** — Scope 阶段必须填写 Decision type / Success criteria / Downstream。后续所有步骤以 success criteria 为筛选依据。
2. **原始素材** —— `raw/` 允许对原始素材做低损清洗和格式规范化，但不得改变来源事实。若需提炼，在 `refined/` 中创建新文件。
3. **raw 文件不删除** —— 在整个研究生命周期内，raw/ 文件保留。未贡献到提炼笔记的 raw 文件在 findings.md 中标注，但不物理删除。
4. **用户 URL 是强制性的** —— 用户主动提供的 URL 必须获取。穷尽工具阶梯，需要登录则暂停请求用户协助。不可静默跳过。
5. **精炼笔记保持原子性** —— 每个发现一个文件，不超过 120 行。超出则拆分。
6. **不做决策** —— research 只描述选项、约束、先例。在其中做选择是 spec 的工作。此处不应出现"我们应该用 X"这样的表述；应使用"X 可用，Y 可用，权衡如下：……"替代。
7. **开放问题是一等公民** —— 每次研究必须以明确的未解决问题清单收尾。空清单意味着研究深度不够。
8. **不自动推进** —— 生成 `findings.md` 后停止。由用户决定下一步。
9. **Wiki 链接是可选提示** —— research 笔记可以引用 `[[wiki-page]]`，但不能依赖 wiki 的存在。若 wiki 中没有对应页面，保留纯文本名称即可。
10. **摄入由用户触发** —— `findings.md` 仅*建议*哪些条目值得摄入。摄入操作本身通过 `wiki` skill 执行，需显式调用。不做 wiki 类型分类——分类是 wiki 技能的职责。
11. **数据获取是策略阶梯，不是单次调用** —— 当 Collect 涉及外部 URL 时，遵循 [references/data-collection.md](references/data-collection.md)。按失败信号升级工具，不按预设分类选择。静默丢弃 URL 是被禁止的。
12. **迭代是允许的** —— Refine 后发现信息缺口 → 回到 Collect 补充。发现范围需要调整 → re-scope。不需要从零开始。
13. **证据冲突如实记录** —— 多个来源说法矛盾时在 refined 笔记中使用 `## Conflicting evidence` 段记录，不在 research 阶段裁定对错。

## 初始化

若 `.claude/research/` 不存在，首次使用时静默创建。

每次新研究，创建 `.claude/research/<topic>/` 并输出：

```
📁 .claude/research/<topic>/ 已创建
   Intent: <decision-type> → <downstream>
   下一步: 定义 question.md (scope + intent anchor)
```

## 本 skill 不做的事

- 不选择设计方案/不做备选方案取舍（使用 `spec` skill）
- 不产出任务或代码（使用 `task` / `impl` skill）
- 不自动将发现摄入 wiki（由用户通过 `wiki` skill 触发）
- 不依赖前置阶段 —— `research` 可以随时冷启动

## 何时不激活

- 用户已有明确 spec 并要求产出任务 → 使用 `task` skill
- 用户提出的是无需探索即可回答的单一问题 → 直接回答
- 用户正在 impl 中途询问代码层面的解释 → 内联回答，不开启 research 文件夹
- research 文件夹已存在且 `findings.md` 内容仍有效 → 直接读取，不重新收集

## 反模式（请勿这样做）

详见 [references/anti-patterns.md](references/anti-patterns.md)。快速清单：

- 意图未锚定就开始收集（缺少 success criteria）
- 在 `raw/` 和 `refined/` 尚未生成之前就写 `findings.md`
- 收集超出已声明范围的素材
- 在精炼笔记中嵌入设计决策
- 在结束时自动触发 spec skill
- 产出单个 500 行的 `research.md`（必须拆分到 `raw/` + `refined/` 中）
- 删除 raw 文件（破坏审计链和迭代能力）
- 静默跳过用户提供的 URL
- 为 wiki 摄入候选做类型分类（那是 wiki 技能的职责）
