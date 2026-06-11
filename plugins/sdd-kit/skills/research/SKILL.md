---
name: research
description: "Index-first requirement exploration workspace for ambiguous needs before freezing them into a package-local PRD via brainstorm. Maintains `.arbor/research/<topic>/` with index.md / log.md / raw/ / notes/. Invoke only on explicit user request."
---

# Research — index-first 需求探索工作区

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

Research 是**发散 → 收敛**阶段：收集原始素材、通过提问澄清需求、带来源地整理理解，把模糊需求推进到"足够收敛，值得进入 brainstorm"。它不做最终设计决策，不自动推进，`brainstorm` 才负责冻结 PRD。

```text
[research] → brainstorm → impl → review
    ↑
    └── 可在任何时候回到 research，继续补资料 / 提问 / 修正理解
```

## Hard rules

1. `index.md` 是唯一入口；每轮都更新。
2. `raw/` 只放带来源的原文摘录，不写解释与决策。
3. `notes/` 是主题化解释层，每篇必须回答"这对需求意味着什么"。
4. 用户提供的 URL 强制获取；需登录时停下请求用户协助，不静默跳过。
5. 不做最终设计决策，不写项目策略，不自动 ingest 到 wiki。
6. Research intent 不清晰时 Clarify 优先于 Collect。

## 何时不激活

- 用户已有清晰需求并要求冻结执行范围 → 用 `brainstorm`。
- 无需建立工作区即可回答的单一事实问答 → 直接回答。
- impl 中途询问局部代码解释 → 内联回答。
- 已存在仍有效的 research 工作区 → 直接读取并继续。

## 工作区产物

```
.arbor/research/<topic>/
├── index.md   # 唯一入口：当前理解 / 范围 / 主题导航 / readiness
├── log.md     # 追加式：每轮做了什么、理解怎么变
├── raw/       # 原文摘录（带 url / tool / fetched_at）
└── notes/     # 主题化解释笔记（每篇带来源 + 含义）
```

文件内容契约见 [`references/content-contract.md`](references/content-contract.md)。

## 六原语

原语可回环调用，不是线性流程。

### ❓ Clarify
**目标**：把模糊需求切到 research question + 候选理解 + 未解歧义。
**产物**：`index.md` 更新；理解显著变化时 `log.md` 加一条。
**How**：暂定性重述需求 → 列已知 / 未知 / 候选 / 歧义 → 若有 1-3 个高杠杆问题就用 `AskUserQuestion` 问（推荐项放第一，description 里说明推荐理由）。

若 topic 涉及当前代码库既有领域，先用 `sdd-wiki collect --query "<topic>" --limit 5 --json` 查已有沉淀，避免重复研究；纯外部资料探索可跳过。

### 📥 Collect
**目标**：收集原始素材到 `raw/`，保持低损可回溯。
**产物**：`raw/<source>.md`，含 frontmatter `url` / `tool` / `fetched_at`。
**How**：用户 URL 强制获取；代码扫描 → `raw/codebase-<area>.md`；新信号出现时回 Clarify 或 Reframe。

详细工具阶梯、分页 / 标签 / 失败处理见 [`references/data-collection.md`](references/data-collection.md)。

### 📝 Note
**目标**：按主题整理 `raw/` 成 `notes/<subtopic>.md`。
**产物**：每篇含结论 / 来源 / 对需求的含义 / 未解问题 / 相关笔记。
**How**：读 `raw/` → 按主题分组 → 每主题一笔；允许对比解释，不允许最终拍板。

### ✅ Check
**目标**：判定当前是否足够进入 brainstorm。
**产物**：`index.md` 的 readiness 更新。
**How**：回答四问——已明确什么 / 仍并存的候选 / 仍阻塞 brainstorm 的歧义 / 当前资料是否够 brainstorm 接手。不够就说清下一轮做什么；够了可置 `status: ready-for-brainstorm`（不自动推进）。

### 📐 Reframe
最初问题或边界失效时更新 `index.md` / `log.md`；保留既有 `raw/` 与 `notes/`，必要时标注哪些被新理解修正。

### 📤 Snapshot
刷新 `index.md` 与 `log.md`，设定 status：
- `open`：后续还会继续。
- `ready-for-brainstorm`：可以进入 brainstorm（不自动推进）。
- `closed`：用户明确认可本轮已完成。

若本轮收集了第三方 API / 平台限制 / 外部系统行为等有长期复用价值的外部知识，提醒用户是否用 wiki skill 沉淀为 `type: source / entity` 页面。

## Subagent fan-out（可选）

仅当 research intent 已明确、存在多个互不依赖分支时使用；主会话负责审计 packet 是否写入 workspace。详见 [`references/workflow.md`](references/workflow.md) 中的 Collect 段。

## 反模式

常见反模式（决策偷运进 notes/、自动推进到 brainstorm、raw 文件被覆盖、未 framing 就并行收集等）见 [`references/anti-patterns.md`](references/anti-patterns.md)。

## Scope

- 不冻结方案、不做最终设计选择（用 brainstorm）。
- 不拆执行计划、不写代码（用 brainstorm / impl）。
- 不自动 ingest 到 wiki（用 wiki skill）。
