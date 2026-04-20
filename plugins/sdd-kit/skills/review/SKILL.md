---
name: review
description: "Independent semantic audit of impl output against spec, task, wiki, and actual git diff. Runs AFTER impl reports DONE/DONE_WITH_CONCERNS. Read-only — never edits code, spec, or task. Reports with a strict 4-state machine (APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT). Appends to task file's `## Review log` (separate from Status log). Must consult git diff; impl self-check is not a substitute. Invoke only on explicit user request (e.g. '用 review skill 审计 <task-id>')."
---

# Review — 独立语义审计

审计 impl 的 DONE 声明是否真正满足了 spec。impl 的 SelfCheck 只能证明验收命令通过；review 提出更深层的问题：**所构建的内容是否与规格说明一致？**

## 在五阶段工作流中的定位

```
research → spec → task → impl → [review]
                           │        │
                           ▼        ▼
                       self-check   semantic audit
                       (acceptance  (spec ↔ diff ↔ wiki)
                        commands)
                           │        │
                           └─► status log    └─► review log
                               (in task file)    (same file, separate section)
```

Review 是**语义安全网**。它：

- 读取 spec + task + status log + **实际 git diff** +（可选）wiki
- 将实现与 spec 语义进行比对，而非仅对照验收条件
- 输出四态审计结果
- **不**编辑代码、spec 或 task
- **不**自动触发任何操作

## 为什么 review 是独立 skill（而非 impl 的一部分）

Impl 的作用域被限定为**仅关注 task**。从设计上它无法：

- 发现代码静默偏离 spec 约束的情况
- 注意到验收通过但 spec 的非功能性需求（SLO、安全）未满足
- 查阅与本次变更相关的 wiki 注意事项
- 交叉检查 git diff 以发现 task 未提及的范围蔓延

在 impl 内部运行这一更广泛的检查会干扰其"翻译者"角色，并迫使其要么越权、要么走过场。分离让每个 skill 各司其职。

## 三个原语

匹配用户意图；完整流程参见 [references/workflow.md](references/workflow.md)。

### 🔍 Collect — 收集审计上下文

触发词："review T-003"、"audit impl 结果"、"check if this matches spec"。

> **推理强度**：🥐 **轻**。纯收集阶段：读取文件、运行 `git diff`、可选查阅 wiki。不做判断。

流程：

1. 确定审计目标：task ID（`T-003`）或 task 文件路径或最近的 DONE 状态行
2. 读取 task 所对应的 spec（`.claude/specs/<name>.md`）
3. 读取 task 条目及其完整 Status log 历史
4. 运行 `git diff <base>..HEAD -- <changed-files>` 查看 impl 实际变更内容
5. 可选查阅 wiki 中相关的 `[[gotcha-*]]` / `[[decision-*]]` 页面（用户引导，非全面扫描）

### ⚖️ Judge — 将 diff 与 spec 进行比对

触发：在 Collect 之后。这是本 skill 的核心。

> **推理强度**：🍞 **重**。在可用时启用扩展思考 / "think harder"。这是本 skill 值得其 token 预算的地方。尽可能在**全新上下文**（新会话 / 子代理）中执行 review——复用编写代码时的上下文会使审计失效。

流程（详见 [references/workflow.md](references/workflow.md#judge)）：

1. 检查 spec 的 **goal** 是否被 diff 覆盖（不仅限于验收命令）
2. 检查 spec 的 **non-goals** 是否未被违反（范围蔓延）
3. 检查 spec 的 **hard constraints**（速率限制、SLO、不变量、安全）是否被满足或在 diff 中被明确处理
4. 检查 spec 的 **interface contract** 是否与代码暴露的接口一致
5. 交叉检查 wiki 中 diff 所涉及领域的 `[[gotcha-*]]` 页面
6. 检查 diff 本身：未测试路径、缺失的错误处理、超出 task 范围的蔓延
7. 将发现归类为四种状态之一

### 📤 Report — 输出审计状态

触发：在 Judge 之后。

> **推理强度**：🥐 **轻**。按照固定状态机分类；发现已在 Judge 阶段产出。

流程（参见 [references/state-machine.md](references/state-machine.md)）：

1. 归类为：APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT
2. 将审计行追加到 task 文件的 `## Review log` 部分（如不存在则创建）
3. 向用户输出结构化摘要，并给出明确的下一步指引
4. **若状态为 `SPEC_DRIFT`**：建议回到 spec skill 进行对齐，而非重新运行 impl

## 四种审计状态

完整定义参见 [references/state-machine.md](references/state-machine.md)。快速参考：

| 状态 | 含义 |
|------|------|
| **APPROVED** | Diff 覆盖了 spec 的 goal，未违反 non-goals，满足 hard constraints。无保留意见。 |
| **APPROVED_WITH_NOTES** | 与 APPROVED 相同，但审计者标记了次要问题（风格、边界情况、后续建议）。不阻塞。 |
| **NEEDS_REWORK** | Diff 与 spec 存在语义差距（缺失约束、行为错误、必需路径未测试）。Impl 需重新处理。 |
| **SPEC_DRIFT** | Diff 看似合理，但 spec 本身有误/不一致/不可行。应退回 spec skill，而非 impl。 |

## 审计行格式

精确格式，追加到 task 文件的 `## Review log` 部分：

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; constraints OK; diff clean
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — passes but: hard-coded timeout 5s (spec said "configurable"); follow-up suggested
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec requires rate-limiting 10/s; diff has no rate-limit middleware; src/webhooks/xhs-handler.ts:1-80 audited
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec says "use redis for idempotency"; codebase has no redis dep; spec is wrong or research is missing
```

复选框语义：

- `[✓]` — APPROVED
- `[~]` — APPROVED_WITH_NOTES
- `[✗]` — NEEDS_REWORK
- `[!]` — SPEC_DRIFT

## Review log 部分（在 task 文件中）

Review log 位于与 impl 的 Status log **相同的** task 文件中，但在**独立的**部分：

```markdown
# <task file header>

## Tasks
...

## Status log
- [x] T-003 (DONE) — 2025-04-18 14:20 — all acceptance cmds green (3/3)

## Review log
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; constraints OK; diff clean
```

如果 `## Review log` 部分不存在，review 在 `## Status log` 下方创建该部分。

## 核心规则

1. **只读** — review 绝不编辑代码、spec、task 定义或验收条件。仅追加到 `## Review log`。
2. **必须读取实际 diff** — `git diff` 是强制性的。仅读取 task 的"验收通过"状态行不构成 review；那只是在重复 impl 的自我检查。
3. **优先使用全新上下文** — 如有可能，在新会话 / 子代理中执行 review。由编写代码的同一参与者在同一会话中进行的 review 是最弱的审计形式。
4. **范围：spec + diff + wiki** — 不要重新读取 research 阶段的原始笔记；那些是 spec 的上游。如果 spec 不清晰，那是 SPEC_DRIFT 的信号，而非 review 的失败。
5. **未经列举检查项不得批准** — APPROVED 必须至少引用：goal ✓、non-goals ✓、constraints ✓、diff scope ✓。空洞的"LGTM"是反模式。
6. **SPEC_DRIFT 退回 spec，而非 impl** — 如果 spec 本身有误，返工必须从 spec 阶段开始；对有缺陷的 spec 重新运行 impl 只会重蹈覆辙。
7. **每次 DONE / DONE_WITH_CONCERNS 的 impl 运行对应一次 review** — 每条 review 行引用其审计的具体 impl 状态行。
8. **不自动重复触发** — review 报告一次后即停止。由用户决定是否退回 impl（NEEDS_REWORK）或 spec（SPEC_DRIFT）。

## 目录结构

Review 不创建新目录。它仅写入：

```
.claude/tasks/<name>.tasks.md        # appends to ## Review log section
```

可选（若用户需要持久化的多次审计记录）：

```
.claude/reviews/<name>.review.md     # only on user request
```

## 初始化

如果目标 task 文件不存在：拒绝并给出明确提示，指向 `task` skill。
如果目标 task 没有 DONE/DONE_WITH_CONCERNS 状态行：拒绝——"nothing to review yet"。

## 本 skill 不做的事

- 不编辑代码 — 发现仅被报告，修复是 impl 的工作（下一轮）
- 不编辑 spec — SPEC_DRIFT 是信号，不是行动
- 不重新运行验收命令 — impl 的 SelfCheck 在机械层面可信
- 不重新分解 task — task skill 负责分解
- 不阻塞 commit/merge — 它仅输出状态；由用户决定行动

## 何时不激活

- Impl 尚未对 task 报告 DONE 或 DONE_WITH_CONCERNS — 无内容可审计
- Task 仍处于 NEEDS_CONTEXT 或 BLOCKED 状态 — 先解决这些问题
- 无 task 文件的临时 impl — 退化为轻量 review（读取 diff + 用户陈述的目标）

## 反模式

参见 [references/anti-patterns.md](references/anti-patterns.md)。快速列表：

- 不列举检查项就盖章 APPROVED
- 仅读取 task 文件（而非 git diff）
- 将"验收通过"等同于"满足 spec"
- 编辑代码来"修复"review 发现的问题（那是 impl 下一轮的工作）
- 将 NEEDS_REWORK 降级为 APPROVED_WITH_NOTES 以避免第二轮 impl
- 在未对照 diff 检查 hard constraints（SLO / 安全）的情况下声称 APPROVED
- 使用编写代码时的同一会话上下文（自我审查偏差）
