---
name: research
description: "Bounded exploration of a topic before committing to a spec/design. Produces `.claude/research/<topic>/` with raw materials, refined notes, and a `findings.md` summarizing discoveries + open questions + wiki-ingest candidates. Does NOT make design decisions (spec skill's job) and does NOT auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — 需求信息探索

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

## 四个原语

根据用户意图匹配对应原语；完整流程见 [references/workflow.md](references/workflow.md)。

### 🎯 Scope — 定义问题边界

触发词："调研 X"、"研究一下 X"、"想做 X 先探索"。

流程（详见 `references/workflow#scope`）：

1. 用一句话复述研究问题
2. 列出范围内事项（2-4 项）
3. 列出明确排除的事项（防止范围膨胀）
4. 点明本次研究所服务的决策点（不包含决策本身）
5. 使用模板 [assets/templates/question.md](assets/templates/question.md) 生成 `question.md`

### 📥 Collect — 收集原始素材

触发词："收集 X 的资料"、"看一下代码里 X 怎么做的"，或用户粘贴文档/URL。

流程：

1. 接收原始输入（粘贴的文档、URL、截图、代码片段）→ `raw/`
2. 扫描代码库中相关入口 → 提取最小化引用，保存为 `raw/codebase-<area>.md`
3. 对于 URL 类输入，遵循 [references/data-collection.md](references/data-collection.md) 中的工具矩阵、完整性规则和失败处理策略。保存到 `raw/ext-<name>.md`（或按该文档说明的分页/分标签变体命名）。
4. **此时不做研究性提炼**。允许对原始素材做低损清洗和格式规范化，但不得改变来源事实、不得合并判断、不得产出设计结论。
   对 HTML / API 文档 / 网页材料，`raw/` 中保存的是 cleaned source note：
   - 删除导航栏、页脚、脚本、样式、广告、cookie banner、重复菜单等展示噪音
   - 保留接口路径、HTTP 方法、参数、headers、认证方式、请求/响应示例、错误码、状态码、分页、rate limit、retry 语义、版本信息、注意事项
   - 将表格、列表、代码块转换为 Markdown
   - 记录来源 URL、抓取时间、清洗方式、被移除内容类型
   - 不得把多个来源综合成结论；综合分析只允许出现在 `refined/`。

### 🔍 Refine — 提炼为聚焦笔记

触发词："整理一下"、"把收集到的提炼一下"。

流程：

1. 针对每个独立发现，写一篇短文 `refined/<topic>.md`（不超过 80 行）
2. 每篇精炼笔记包含：发现了什么 / 来源在哪里 / 为什么重要 / 引出了什么开放问题
3. 丢弃未贡献到任何精炼笔记的原始素材（不保留噪音）
4. 应用模板 [assets/templates/finding-note.md](assets/templates/finding-note.md)

### 📤 Propose — 呈现发现 + 摄入建议

触发词："总结一下 research"、"research 完了"、"可以结束研究了"。

流程：

1. 使用模板 [assets/templates/findings.md](assets/templates/findings.md) 生成 `findings.md`
2. 列出核心发现（链接到 `refined/` 笔记）
3. 列出开放问题（供 spec 解决）
4. 列出 **wiki 摄入候选**："以下发现若要沉淀为长期知识，建议 ingest" —— 不自动执行摄入
5. 输出收尾摘要；**不调用** spec skill

## 目录结构

```
.claude/research/<topic>/
├── question.md                  # 范围 + 排除项 + 所服务的决策
├── raw/                         # 原始收集，低损清洗和格式规范化
│   ├── codebase-<area>.md       # 来自代码的引用，含 file:line 引用
│   ├── ext-<source>.md          # 外部材料摘要
│   └── user-input-YYYY-MM-DD.md # 用户粘贴的材料
├── refined/                     # 提炼后的发现，每个话题一个文件
│   ├── <finding-1>.md
│   └── <finding-2>.md
└── findings.md                  # 总结 + 开放问题 + 摄入候选
```

`<topic>` 使用 kebab-case 命名，按话题命名（不使用日期）。示例：`.claude/research/xhs-customer-webhook/`。

## 核心规则

1. **原始素材** —— `raw/` 允许对原始素材做低损清洗和格式规范化，但不得改变来源事实。若需提炼，在 `refined/` 中创建新文件。
2. **精炼笔记保持原子性** —— 每个发现一个文件，不超过 80 行。超出则拆分。
3. **不做决策** —— research 只描述选项、约束、先例。在其中做选择是 spec 的工作。此处不应出现"我们应该用 X"这样的表述；应使用"X 可用，Y 可用，权衡如下：……"替代。
4. **开放问题是一等公民** —— 每次研究必须以明确的未解决问题清单收尾。空清单意味着研究深度不够。
5. **不自动推进** —— 生成 `findings.md` 后停止。由用户决定下一步。
6. **Wiki 链接是可选提示** —— research 笔记可以引用 `[[wiki-page]]`，但不能依赖 wiki 的存在。若 wiki 中没有对应页面，保留纯文本名称即可。
7. **摄入由用户触发** —— `findings.md` 仅*建议*哪些条目值得摄入。摄入操作本身通过 `wiki` skill 执行，需显式调用。
8. **数据获取是策略阶梯，不是单次调用** —— 当 Collect 涉及外部 URL 时，遵循 [references/data-collection.md](references/data-collection.md)。静默丢弃 URL（例如"curl 失败，跳过"）是被禁止的。标签页、分页、一级引用文档、主要资源必须按该文档要求覆盖。无法获取的来源必须显式记录为 `raw/ext-<name>-failed.md`，并在 `findings.md` 的开放问题中标注。

## 初始化

若 `.claude/research/` 不存在，首次使用时静默创建。

每次新研究，创建 `.claude/research/<topic>/` 并输出：

```
📁 .claude/research/<topic>/ 已创建
   下一步: 定义 question.md (scope + out-of-scope)
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

- 在 `raw/` 和 `refined/` 尚未生成之前就写 `findings.md`
- 收集超出已声明范围的素材
- 在精炼笔记中嵌入设计决策
- 在结束时自动触发 spec skill
- 产出单个 500 行的 `research.md`（必须拆分到 `raw/` + `refined/` 中）
