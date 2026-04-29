---
name: review
description: "Independent semantic audit of impl output for a package-local T-xxx against package-local PRD, task, wiki, and actual package diff. Runs AFTER impl reports DONE/DONE_WITH_CONCERNS. Read-only — never edits code, `prd.md`, or task definition. Reports APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT. Appends to `.arbor/tasks/<name>/review.md` and updates lifecycle through `sdd-arbor`. A single T-xxx approval is not package PR approval. Must consult git diff. Invoke only on explicit user request (e.g. '用 review skill 审计 <package> 的 T-001')."
---

# Review — 独立语义审计

审计 impl 的 DONE 声明是否真正满足了 package-local PRD + task。impl 的 SelfCheck 只能证明验收命令通过；review 提出更深层的问题：**所构建的内容是否与上游意图一致？**

## 在五阶段工作流中的定位

```text
research → brainstorm → task → impl → [review]
                                 │        │
                                 ▼        ▼
                             self-check   semantic audit
                           (acceptance) (prd ↔ task ↔ diff ↔ wiki)
```

Review 是**语义安全网**。它：

- 读取 package-local `prd.md` + task definition + task state (`task.json`) + `context/review.jsonl` + **实际 git diff** +（可选）wiki
- 将实现与上游语义进行比对，而非仅对照验收条件
- 输出四态审计结果
- **不**编辑代码、`prd.md` 或 `task.md` 任务定义
- **不**自动触发任何操作

## 三个原语

### 🔍 Collect — 收集审计上下文

1. 确定审计目标：package + package-local T-xxx；裸 `T-001` 不可视为全局唯一任务
2. 读取 task package 的 `prd.md`、`task.md`、`task.json` 与可选 `context/review.jsonl`
3. 运行 `git diff` 查看 package branch/worktree 的实际变更，并说明当前 T-xxx 对应的 diff scope
4. 可选用 `sdd-arbor wiki-collect --query "<query>" --limit 5 --json` 查阅相关 wiki 页面；wiki 只作 orientation，结论必须回到 diff / PRD / task / `.arbor` 验证
5. 若 package 内缺少 `prd.md`，可读取 legacy `.arbor/brainstorms/<name>.md` 作为 fallback，但必须报告这是迁移风险

### ⚖️ Judge — 将 diff 与上游语义进行比对

1. 检查 PRD 的目标 / 范围 / 场景是否被 diff 覆盖
2. 检查 task 的 deliverable / acceptance / context / ready-check 是否被尊重
3. 检查 diff 是否出现范围蔓延、遗漏关键路径、违背来源支持的约束
4. 检查 wiki gotcha 是否被违反
5. 若任务带 `source_amendment`，确认 AMD corrected rule 被实现，且 regression checks 覆盖未受影响旧行为
6. 将发现归类为一个状态

### 📤 Report — 输出审计状态

1. 分类为：APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT
2. 追加到 `.arbor/tasks/<name>/review.md`
3. 使用 `sdd-arbor` 更新 `.arbor/tasks/<name>/task.json` 中对应 T-xxx 的 `state`、`updated_at`、顶层聚合 `state/current_phase/next_action` 与 `phase_history`
4. 输出结构化摘要，并说明此 verdict 是否只覆盖当前 T-xxx
5. 若所有 required T-xxx 都已通过 review，说明 package 可进入 PR/final review；否则继续处理下一个 T-xxx
6. 若有新的 review context，使用 `sdd-arbor add-context` / `sdd-arbor add-context-batch --type review` 追加，不手写 `context/*.jsonl`
7. 若状态为 `BRAINSTORM_DRIFT`：建议回到 brainstorm 追加 package-local `AMD-xxx`，再由 task 追加新的 T-xxx；不要让 impl 背锅

## 四种审计状态

| 状态 | 含义 |
|------|------|
| **APPROVED** | Diff 中当前 T-xxx 对应部分覆盖了 PRD slice 与 task 范围，无保留意见 |
| **APPROVED_WITH_NOTES** | 语义正确，但有轻微问题或后续建议 |
| **NEEDS_REWORK** | Diff 与 PRD / task 存在语义差距，impl 需重新处理 |
| **BRAINSTORM_DRIFT** | Diff 看似合理，但 PRD 本身有误 / 失效 / 与当前代码库脱节 |

## 核心规则

1. **只读代码和任务定义** —— review 绝不编辑代码、`prd.md`、`task.md` 或验收条件；只可追加 `review.md`，并必须通过 helper 更新 `task.json` 的 review 元数据。
2. **`task.json` 是当前状态源** —— `review.md` 是审计日志，latest review result 以 `task.json` 为准。
3. **必须读取实际 diff** —— 只看 task 的 DONE 状态不构成审查；diff 是 package branch/worktree diff，结论要聚焦当前 T-xxx。
4. **单个 T-xxx 批准不等于 package PR 批准** —— package readiness 由所有 required T-xxx review 聚合而来。
5. **优先使用全新上下文** —— 如有可能，在新会话 / 子代理中执行 review。
6. **范围：PRD + task + diff + wiki** —— research 是上游背景，不是审查主要对象。
7. **未经列举检查项不得批准** —— APPROVED 必须至少说明 goal / scope / constraints / diff scope。
8. **BRAINSTORM_DRIFT 退回 brainstorm，而非 impl** —— 上游 PRD 错误时，追加 AMD-xxx，再 task append 新 T-xxx。
9. **Amendment review 要看回归** —— 审 amendment-linked T-xxx 时必须确认 corrected rule + regression evidence。
10. **不自动重复触发** —— 报告一次后即停止。
11. **不手写 JSON 状态或 context JSONL** —— 状态用 helper；context 用 `add-context` / `add-context-batch`；如 helper 不足，先扩展 helper。
