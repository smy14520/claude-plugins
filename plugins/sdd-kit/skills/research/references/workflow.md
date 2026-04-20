# Research 工作流：范围界定 / 收集 / 提炼 / 提议

四个原语的详细流程。SKILL.md 给出高层步骤；本文件提供包含边缘情况在内的完整工作流。

---

## 范围界定（Scope）

在接触任何资料之前先框定问题。没有声明范围的研究会变成无边界浏览。

### 触发短语

- "研究一下 X" / "调研 X"
- "想做 X 先探索"
- "X 之前有人做过吗，看看"
- "do research on X" / "explore X"

### 完整流程

**步骤 1 — 提取主题**

从用户的表述中提取：

- 主题名称（一个名词短语）→ 以 kebab-case 作为 `<topic>` 目录名
- 喂养决策（这次研究的结论将影响什么决策？）

如果喂养决策不明确，问一个问题："这个研究的结论会影响什么决策？是想选型、估工、还是理解现有代码？"

**步骤 2 — 撰写 `question.md`**

从 [../assets/templates/question.md](../assets/templates/question.md) 加载模板。填写：

- **Question**：单句表述
- **In scope**：2-8 个要点，具体的子问题
- **Out of scope**：2+ 个要点，明确的排除项（关键——这是防止范围膨胀的手段）
- **Feeding decision**：哪个 spec/task 将消费此次研究
- **Time budget**：用户的大致估算（可选，但有帮助）

**步骤 3 — 输出摘要**

```
📁 .claude/research/<topic>/question.md 已创建
   In scope: X, Y
   Out of scope: Z
   下一步: collect (粘贴资料 / 告诉我从哪里开始看)
```

### 边缘情况

**情况：用户尚未缩小范围**

不要猜测。问一个问题："你希望这次 research 主要回答什么？" 然后填写。

**情况：用户给的范围很大（如"研究一下前端架构"）**

建议收窄范围："这个范围很大。建议先限定在一个具体问题（如 '如何组织 shared UI components'），回头再扩展。OK 吗？"

---

## 收集（Collect）

将原始资料归入 `raw/`。此处不做提炼。

### 触发短语

- 用户粘贴文档、URL、截图
- "看一下代码里 X 怎么做的"
- "收集 X 的资料"

### 完整流程

**步骤 1 — 对输入进行分类**

- 粘贴的文档/文本 → `raw/user-input-YYYY-MM-DD.md`
- URL → 抓取，简要概述（不是提炼），保存为 `raw/ext-<slug>.md`
- 代码阅读请求 → 扫描，保存相关引用（含 file:line 参考）为 `raw/codebase-<area>.md`

**步骤 2 — 按最小结构写入 raw 文件**

每个 raw 文件包含：

```markdown
# <标题>

> Source: <URL | path | user>
> Collected: YYYY-MM-DD

## Content

<原文或近乎原文的摘录>
```

**步骤 3 — 收集阶段不要提炼**

诱惑：阅读代码时，你看到了某种模式，想写下"这里使用了 X 模式"。忍住。将摘录放入 `raw/`；提炼步骤会决定是否需要抽象。

**步骤 4 — 跟踪已收集内容**

每次收集操作后，输出：

```
📥 Collected: raw/<file>.md
   已有 raw 文件: N 个
   建议: 继续收集 / 开始 refine
```

### 边缘情况

**情况：用户提供了一个非常长的 URL/文档**

抓取整个文档。抓取并概述至 200 行以内，保留重点内容，注明省略了哪些内容。保留原始 URL 的醒目位置。

**情况：扫描发现代码库中没有相关内容**

写一行 `raw/codebase-<area>.md`："Scanned `<paths>`，no relevant matches for `<topic>`。"

**情况：用户想跳过收集直接进入提炼**

仅在用户粘贴的是已经整理过的资料时才允许。警告："跳过 collect 意味着没有原始引用链路。你确定这些资料已经是提炼过的？"

---

## 提炼（Refine）

将原始资料提炼为聚焦的 `refined/<topic>.md` 笔记。

### 触发短语

- "整理一下"
- "把收集到的提炼一下"
- "refine 一下"

### 完整流程

**步骤 1 — 按发现分组 raw 文件**

阅读所有 `raw/*.md`。按发现所支撑的*发现*分组，而非按来源分组。

示例：三个不同 raw 文件中提到的签名 → 全部汇入一个 `refined/xhs-signature-scheme.md`。

**步骤 2 — 每个发现写一条提炼笔记**

应用 [../assets/templates/finding-note.md](../assets/templates/finding-note.md)。必需的章节：

- **What I found**：具体发现（1-3 句话）
- **Where**：引用回 `raw/` 文件并附带行号
- **Why it matters**：这如何影响喂养决策
- **Open question**：该发现之后仍然未知的内容

硬性限制：每条笔记不超过 80 行。超长则拆分。

**步骤 3 — 丢弃未使用的 raw**

没有贡献给任何提炼笔记的 raw 文件：

- 如果后续可能有用 → 保留
- 如果明显无关 → 删除或移至 `raw/.discarded/`

永远不要在没有明确下游用途的情况下"以防万一"保留 raw 文件。

**步骤 4 — 输出提炼摘要**

```
🔍 Refined: N 个 refined notes
   - <finding-1> → <note-1>.md
   - <finding-2> → <note-2>.md
   未用 raw 文件: M 个 (保留 / 丢弃)
```

### 边缘情况

**情况：一个发现想变成决策**

如果提炼时你觉得"这个发现其实就是我们的选择"，停下。Research 不做决策。改写为选项描述：

- ❌ "We should use webhook"
- ✅ "Webhook is available. Poll is also available. Tradeoffs: ..."

**情况：一个发现过于抽象，无法引用**

未经验证的发现不是发现。要么引用来源，要么丢弃。

---

## 提议（Propose）

收尾研究。生成 `findings.md` + wiki 摄取候选项。

### 触发短语

- "总结一下 research"
- "research 完了"
- "可以结束研究了"
- "closing the research"

### 完整流程

**步骤 1 — 撰写 `findings.md`**

应用 [../assets/templates/findings.md](../assets/templates/findings.md)。必需的章节：

- **Question**（从 question.md 复制）
- **Key findings**（不超过 7 个要点，每个链接到一条 `refined/` 笔记）
- **Open questions**（供 spec 解决——明确列表，仅当确实没有未决问题时才可为空）
- **Ingest candidates**——哪些提炼笔记值得提升至 wiki
- **Ephemeral**——哪些提炼笔记仅限本次决策范围（不会被摄取）

**步骤 2 — 按建议的 wiki 类型对摄取候选进行分类**

对每个候选项，建议 wiki 页面类型（按照 wiki skill）：

- `entity` — 描述项目中的真实对象
- `concept` — 可复用的抽象
- `gotcha` — 特定场景 + 错误 + 修复
- `decision` — 捕获选择及其理由（通常在 spec 之后、而非 research 期间变成决策页面）
- `source` — 外部原始资料的摘要

**步骤 3 — 不要自动摄取**

明确告知用户：

> 以上 ingest 建议仅为提议。若要真正写入 wiki，请调用 `wiki` skill 并 ingest 具体条目。

**步骤 4 — 输出收尾摘要**

```
📤 Research closed: .claude/research/<topic>/findings.md

Key findings: N
Open questions: M
Ingest candidates: K (entity: A, concept: B, gotcha: C)

下一步建议 (用户决定):
- 运行 spec skill 起草方案（open questions 会成为决策点）
- 运行 wiki ingest 沉淀 ingest 候选
- 或两者都做，按顺序由你决定
```

### 边缘情况

**情况：未决问题列表为空**

质疑："研究结束但没有 open question，是研究确实彻底，还是实际上没发散？" 让用户确认后再关闭。

**情况：摄取候选列表为空**

没问题——并非每次研究都会产生可复用的知识。在 findings.md 中注明："本次 research 无 wiki ingest 候选（所有发现均为本次决策 scoped）。"

**情况：用户想之后重新审视/扩展**

在 frontmatter 中将 `findings.md` 标记为 `status: open`。后续会话可以直接追加而无需重写。
