# Research 工作流：范围界定 / 收集 / 提炼 / 提议

四个原语的详细流程。SKILL.md 给出高层步骤；本文件提供包含边缘情况在内的完整工作流。

---

## 范围界定（Scope）

在接触任何资料之前先框定问题并锚定意图。没有声明范围和意图的研究会变成无边界浏览。

### 触发短语

- "研究一下 X" / "调研 X"
- "想做 X 先探索"
- "X 之前有人做过吗，看看"
- "do research on X" / "explore X"

### 完整流程

**步骤 1 — 提取主题和意图**

从用户的表述中提取：

- 主题名称（一个名词短语）→ 以 kebab-case 作为 `<topic>` 目录名
- 意图锚定：
  - Decision type：选型 / 估工 / 理解现状 / 评估可行性
  - Success criteria：什么算"有用的发现"
  - Downstream：spec-name / 直接回答 / wiki 摄取

如果意图不明确，问一个问题："这次研究的结论会影响什么决策？是想选型、估工、还是理解现有代码？"

**步骤 2 — 撰写 `question.md`**

从 [../assets/templates/question.md](../assets/templates/question.md) 加载模板。填写：

- **Question**：单句表述
- **In scope**：2-8 个要点，具体的子问题
- **Out of scope**：2+ 个要点，明确的排除项（关键——这是防止范围膨胀的手段）
- **Intent anchor**：Decision type / Success criteria / Downstream

**步骤 3 — 输出摘要**

```
📁 .claude/research/<topic>/question.md 已创建
   In scope: X, Y
   Out of scope: Z
   Intent: <decision-type> → <downstream>
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
- URL → 判断来源级别（用户提供 vs 研究发现），按 [data-collection.md](data-collection.md) 获取，保存为 `raw/ext-<slug>.md`
- 代码阅读请求 → 扫描，保存相关引用（含 file:line 参考）为 `raw/codebase-<area>.md`

**用户提供的 URL vs 研究发现的 URL**：

- 用户主动粘贴的 URL → 强制获取，穷尽工具阶梯，需要登录则暂停请求用户协助
- 研究过程中发现的 URL → 按意图锚定的 success criteria 判断是否追踪

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

**情况：URL 获取需要登录**

暂停。告知用户："此 URL 需要登录才能访问。请在浏览器中完成登录后告知我，我将继续抓取。" 等待用户确认后用 playwright 继续。不要跳过。

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
- **Why it matters**：这如何影响意图锚定中的决策上下文
- **Open question**：该发现之后仍然未知的内容

可选章节：

- **Conflicting evidence**：多个来源对同一事实给出不同说法时使用

硬性限制：每条笔记不超过 120 行。超长则拆分。

**步骤 3 — 标记未使用的 raw 文件**

没有贡献给任何提炼笔记的 raw 文件：保留在 `raw/` 中，不删除。在 findings.md 中标注为 "unused" 并说明原因。

**步骤 4 — 输出提炼摘要**

```
🔍 Refined: N 个 refined notes
   - <finding-1> → <note-1>.md
   - <finding-2> → <note-2>.md
   未用 raw 文件: M 个 (将在 findings.md 中标注)
```

### 边缘情况

**情况：一个发现想变成决策**

如果提炼时你觉得"这个发现其实就是我们的选择"，停下。Research 不做决策。改写为选项描述：

- ❌ "We should use webhook"
- ✅ "Webhook is available. Poll is also available. Tradeoffs: ..."

**情况：一个发现过于抽象，无法引用**

未经验证的发现不是发现。要么引用来源，要么丢弃。

**情况：多个来源说法冲突**

使用 `## Conflicting evidence` 段记录各方说法和可能原因（版本差异、语境不同、其中一方过时）。不要在 research 阶段裁定谁对——裁定是 spec 的职责。

---

## 完整性检查（Refine → Propose 之间的门控）

提炼完成后，在进入提议之前必须通过完整性检查：

### 检查项

1. **Success criteria 覆盖**：意图锚定的每条 success criteria 是否都有至少一条 refined 笔记回应？如果有 criteria 未被覆盖 → 回到收集补充材料。
2. **未回答的子问题**：question.md 中的子问题是否都被涉及？如果遗漏 → 回到收集。
3. **范围偏移信号**：提炼过程中是否发现了 question.md 的范围需要调整？如果需要 → 执行 re-scope（见下方）。

### 输出

```
✅ Completeness check passed — all success criteria covered
   或
⚠️ Gap: <某条 success criteria> 尚无对应发现
   建议: 回到 Collect 补充 <具体方向>
```

---

## 重新界定范围（Re-scope）

当提炼或完整性检查揭示 question.md 的范围需要调整时。

### 何时触发

- 提炼发现原始问题提偏了（如"研究前端架构"实际需要的是"研究状态管理方案"）
- 排除范围里的内容其实与研究高度相关
- 意图锚定的 success criteria 需要修正

### 流程

1. **不删除旧的 question.md 内容**，而是在 `## Scope history` 表中追加一条变更记录
2. 更新 In scope / Out of scope / Intent anchor
3. 已有的 raw/ 和 refined/ 文件保留，标注哪些是旧范围的产出
4. 输出变更摘要：

```
📐 Re-scoped: <topic>
   变更: <什么从 in-scope 移到了 out-of-scope，或反之>
   原因: <为什么>
   已有文件: N 个 raw, M 个 refined (保留)
```

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
- **Critical findings**（直接影响决策的发现，链接到 refined/ 笔记）
- **Context findings**（提供背景但不直接影响决策的发现）
- **Open questions**（供 spec 解决——明确列表，仅当确实没有未决问题时才可为空）
- **Ingest candidates**——哪些提炼笔记值得提升至 wiki，每个附一句理由（不做 wiki 类型分类）
- **Ephemeral**——哪些提炼笔记仅限本次决策范围

**步骤 2 — 不要自动摄取**

明确告知用户：

> 以上 ingest 建议仅为提议。若要真正写入 wiki，请调用 `wiki` skill 并 ingest 具体条目。

**步骤 3 — 输出收尾摘要**

```
📤 Research closed: .claude/research/<topic>/findings.md

Critical findings: N
Context findings: M
Open questions: K
Ingest candidates: J

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
