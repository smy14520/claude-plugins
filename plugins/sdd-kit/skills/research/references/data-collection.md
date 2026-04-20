# 数据收集策略

Collect 原语的 URL 抓取步骤的详细流程。适用于 `research.Collect` 需要检索 URL（或外部托管产物）并保存至 `raw/ext-<name>.md` 的所有场景。

> **调用来源**：[`../SKILL.md`](../SKILL.md)（Collect 原语，步骤 3）。
> **也被引用自**：`wiki` skill 的 source-* 摄取路径（跨 skill 复用）。

## 核心原则

**抓取是一个策略阶梯，而非单次调用。** 单次 `curl` 失败后回退到"我拿不到这个"是一种反模式。在宣布失败之前，必须穷尽下面的阶梯。

阶梯目标，按优先级排序：

1. **为 URL 类型选择合适工具**（选择能实际成功的最廉价工具）
2. **完整性优先于第一印象**（一个 URL 几乎从不等于一个文件）
3. **明确的失败记录**（永远不要静默丢弃 URL）

---

## 1. 工具调度矩阵

根据 URL 形态和内容特征选择主工具。当主工具无法提取可用内容时使用备选方案。

| URL / 目标形态 | 主工具 | 备选方案 | 主工具选择理由 |
|---|---|---|---|
| GitHub 仓库 — README、源文件、wiki 页面 | `deepwiki` | 直接抓取 `raw.githubusercontent.com` → `playwright` | 预索引且支持语义问答；远比抓取渲染页面经济 |
| 库 / SDK / 框架 API 文档（React, Next.js, AI SDK, Tailwind 等） | `context7` | `playwright` | 专为框架文档检索设计；返回结构化文档段落 |
| 静态 HTML、RSS、已知 JSON API | 内置 fetch（等同 curl） | `playwright` | 最廉价；不要过度工程化 |
| JS 渲染 / SPA / 需要脚本执行 | `playwright` | `js-reverse`（当底层 API 调用可逆向时） | 需要真实浏览器运行时 |
| 标签切换 / 分页列表 / 无限滚动 | `playwright`（逐一导航各状态） | — | 多步导航不可避免 |
| 需要登录 / 认证内容 | `playwright` + 会话复用 | — | 依赖浏览器身份；无替代方案 |
| 时事新闻 / 近期事件 / 实时信息 | `grok-search` | `exa` | `grok-search` 包含时效信号 |
| 不确定确切 URL — 仅有主题 | `exa`（神经 / 语义搜索） | `grok-search` | 先定位，再用找到的 URL 重新进入矩阵 |
| 特定符号 / 函数的 API 参考 | `context7` | `deepwiki`（如果在 GitHub 上） | `context7` 直接返回相关文档段落 |

**工具选择备注：**

- 当 URL 的内容已被结构化/索引化来源（`deepwiki`、`context7`）覆盖时，始终优先使用这些来源而非原始抓取。
- `js-reverse` 是专家级工具：仅在 `playwright` 能获取内容但代价较高（大页面、大量请求），且存在可发现的后端 API 调用（网络面板显示干净的 JSON 端点）时使用。
- `exa` 和 `grok-search` 是发现工具。一旦它们返回 URL，用该 URL 重新进入本矩阵——不要将搜索结果摘要当作最终内容。

---

## 2. 回退阶梯 — 强制执行，非可选

当主工具失败时：

1. 不要放弃。调用备选列中的下一个工具。
2. 如果该行所有工具都失败，记录失败路径（见第 5 节）并生成 `raw/ext-<name>-failed.md` 条目。不要静默省略该 URL。
3. `findings.md` 中面向用户的摘要必须引用尝试过什么以及各自失败的原因。

**反模式**（明确禁止）：

- "curl 返回 403 所以跳过了这个来源" — 必须升级到 `playwright`。
- "这是 SPA 大概很难，跳过" — 仍必须尝试 `playwright`。
- "搜索结果有摘要，我用它当内容了" — 摘要是引子，不是来源。抓取实际 URL。
- "回退链中三个工具失败了两个，我停了" — 尝试第三个。

---

## 3. 完整性规则

单个 URL 几乎从不对应单个 raw 文件。在声明来源收集完成之前，验证以下维度：

### 3.1 标签完整性

如果页面有多个标签（如"概述 | API | 示例 | 讨论"），分别收集每个标签的内容。每个标签一个文件：

```
raw/ext-<name>-overview.md
raw/ext-<name>-api.md
raw/ext-<name>-examples.md
raw/ext-<name>-discussion.md
```

如果某个标签的内容与另一个重复（如"打印视图"与"概述"相同），跳过并在 frontmatter 中加一行注释说明，而非静默丢弃。

### 3.2 分页

对于分页列表（论坛、API 分页结果、"加载更多"按钮）：

- 默认上限：**10 页**（或第一个空页 / 列表结束信号，以先到者为准）。
- 按研究覆盖：在主题的 `question.md` frontmatter 中添加 `fetch.max_pages: N`。适用于该研究的所有分页 URL。
- 停止条件（任一触发即停）：空页 / 与上一页内容相同 / 达到 `max_pages` / 服务器返回 404/410。
- 逐页记录：每页保存为 `raw/ext-<name>-p{N}.md`。不要将多页合并为一个文件——会丢失粒度，难以重新审计。

### 3.3 一级追踪

如果主页明确引用（"另见"、"相关文档"、"引用自"）与研宄问题相关的外部文档，追踪这些链接的**一级**。不要递归。

- 追踪深度：1。
- 追踪到的页面保存为 `raw/ext-<name>-ref-<short>.md`。
- 不要自动追踪纯装饰性的内联超链接（导航菜单、作者简介、页脚）。

### 3.4 资产携带

如果图片、PDF 或其他二进制资产承载主要信息（论文中的图表、教程中的截图），下载至：

```
raw/assets/<topic>/
```

从对应的 `raw/ext-*.md` 中以相对路径引用。不要依赖远程 URL——外部资产会失效。

### 3.5 元数据 frontmatter

每个 `raw/ext-*.md` 文件必须以以下内容开头：

```yaml
---
url: <原始 URL>
tool: <使用的抓取工具，例如 playwright / deepwiki / context7>
fetched_at: YYYY-MM-DD HH:MM
strategy: <简要说明 — 例如 "paginated, 7 pages collected, stopped on empty">
page_of_set: <例如 "3/7" 如果属于分页集，否则省略>
---
```

此元数据使后续审计（spec DRIFT、review）能够将每个断言追溯到带时间戳的检索记录。

---

## 4. question.md 中的覆盖配置

按研究的覆盖配置存放在主题的 `question.md` frontmatter 中：

```yaml
---
status: open
date: YYYY-MM-DD
feeding: <spec-name>

# 可选的抓取覆盖配置：
fetch:
  max_pages: 50               # 默认 10
  follow_depth: 2             # 默认 1；很少需要
  tools_force: [playwright]   # 跳过矩阵，始终使用此工具
  tools_exclude: [js-reverse] # 永不调用此工具
---
```

覆盖配置仅适用于当前研究主题。不改变全局默认值。

---

## 5. 失败处理

当 URL 在穷尽回退阶梯后仍无法检索：

### 5.1 记录，不要丢弃

创建 `raw/ext-<name>-failed.md`：

```markdown
---
url: <URL>
attempts:
  - tool: deepwiki
    error: "not a GitHub URL"
    at: 2026-04-20 14:05
  - tool: playwright
    error: "timeout after 30s, Cloudflare challenge"
    at: 2026-04-20 14:07
  - tool: js-reverse
    error: "no backend API visible in network trace"
    at: 2026-04-20 14:12
final_status: unretrievable
---

# Why this matters

<1-2 行说明此来源预期贡献的内容>

# What the research will proceed with instead

<替代来源或明确的"缺口"确认>
```

### 5.2 传播至 findings.md

在 `findings.md` 的"Open questions"章节中添加：

```markdown
- ⚠️ Could not retrieve [<来源名称>](<URL>) — tried deepwiki, playwright, js-reverse.
  See `raw/ext-<name>-failed.md`. The spec must decide whether to proceed without this
  input or find an alternative source.
```

这确保 spec 阶段不会静默假设"research 已覆盖所有内容"。

### 5.3 永远不要捏造

如果来源不可检索，**不要**从 URL、标题或搜索结果摘要推断其内容。在 raw 层捏造内容会污染所有下游阶段。

---

## 6. 工具调用说明

工具调用因运行时环境而异（MCP server、CLI、内置工具）。以下为指导原则而非严格语法——请根据执行 agent 的可用绑定进行调整。

### deepwiki

用于 GitHub 仓库。典型调用目标是仓库根目录或特定文件路径。返回结构化的问答就绪内容。

### context7

用于库文档。典型调用：指定库名（如 `ai-sdk`、`react`、`tailwindcss`）加主题。返回带版本标签的精选文档片段。

### playwright

用于 JS 渲染内容。典型用法：导航至 URL，等待选择器，提取内容。处理标签：遍历标签触发器。处理分页：点击"下一页"直到满足停止条件。

### js-reverse

用于从前端行为推导后端 API。仅在 playwright 成功但代价较高且站点使用干净 JSON 后端时使用。典型用法：检查网络追踪，识别 API 端点，直接重新抓取该端点。

### grok-search

用于实时 / 近期内容。典型用法：查询短语 + 可选时间窗口。

### exa

用于语义 / 神经搜索。典型用法：主题短语，返回按语义相关性排序的 URL。

### 内置 fetch（等同 curl）

用于静态 HTML / RSS / JSON。遵守 robots.txt；当目标需要时包含 User-Agent 头；5xx 错误重试 2 次后再升级。

---

## 7. 边界 — 何时不使用本文件

本参考文件仅管辖 **Collect** 原语。不适用于：

- **Refine** — 提炼笔记是人工风格的蒸馏，不是重新抓取。
- **Findings** — findings 引用已收集的 raw 资料，不产生新抓取。
- **Spec** — spec 不得抓取；如果 spec 需要数据，这是一个缺口，应将控制权交回 research。
- **Impl** — impl 读取 task 的交付物/验收标准，不是外部 URL。在 impl 阶段获取外部事实 = research 放错了阶段，应弹回 NEEDS_CONTEXT。
- **非 source 页面的 Wiki 摄取** — 仅 `source-*` 页面遵循此流程。Entity / concept / gotcha / decision 页面从已有研究或代码中蒸馏，不需要重新抓取。

---

## 8. 检查清单 — 声明收集完成之前

对于研究输入集中的每个 URL：

- [ ] 已尝试主工具
- [ ] 如果主工具失败，已尝试至少一个备选工具
- [ ] 已验证标签完整性（或确认为单标签页面）
- [ ] 已达到分页上限（或确认为非分页页面）
- [ ] 已完成一级追踪（或确认无实质性引用）
- [ ] 已下载资产（或确认无主要资产）
- [ ] 每个 `raw/ext-*.md` 都有完整的 frontmatter 元数据
- [ ] 失败的 URL 已记录在 `raw/ext-*-failed.md` 中并在 `findings.md` 中披露

如果有任何复选框未勾选，则 Collect 未完成——要么完成该步骤，要么记录跳过的原因。
