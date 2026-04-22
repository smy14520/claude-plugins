---
name: review
description: "Independent semantic audit of impl output against brainstorm, task, wiki, and actual git diff. Runs AFTER impl reports DONE/DONE_WITH_CONCERNS. Read-only — never edits code, brainstorm, or task. Reports with a strict 4-state machine (APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT). Appends to task file's `## Review log` (separate from Status log). Must consult git diff; impl self-check is not a substitute. Invoke only on explicit user request (e.g. '用 review skill 审计 <task-id>')."
---

# Review — 独立语义审计

审计 impl 的 DONE 声明是否真正满足了 brainstorm + task。impl 的 SelfCheck 只能证明验收命令通过；review 提出更深层的问题：**所构建的内容是否与上游意图一致？**

## 在五阶段工作流中的定位

```text
research → brainstorm → task → impl → [review]
                                 │        │
                                 ▼        ▼
                             self-check   semantic audit
                           (acceptance) (brainstorm ↔ task ↔ diff ↔ wiki)
```

Review 是**语义安全网**。它：

- 读取 brainstorm + task + status log + **实际 git diff** +（可选）wiki
- 将实现与上游语义进行比对，而非仅对照验收条件
- 输出四态审计结果
- **不**编辑代码、brainstorm 或 task
- **不**自动触发任何操作

## 三个原语

### 🔍 Collect — 收集审计上下文

1. 确定审计目标：task ID / task 文件 / 最近的 DONE 状态行
2. 读取 task 对应的 brainstorm（首选 `.claude/brainstorms/<name>.md`，兼容 legacy spec）
3. 读取 task 条目及完整 Status log
4. 运行 `git diff` 查看 impl 实际变更
5. 可选查阅相关 wiki 页面

### ⚖️ Judge — 将 diff 与上游语义进行比对

1. 检查 brainstorm 的目标 / 范围 / 场景是否被 diff 覆盖
2. 检查 task 的 deliverable / acceptance / context / ready-check 是否被尊重
3. 检查 diff 是否出现范围蔓延、遗漏关键路径、违背来源支持的约束
4. 检查 wiki gotcha 是否被违反
5. 将发现归类为一个状态

### 📤 Report — 输出审计状态

1. 分类为：APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT
2. 追加到任务文件的 `## Review log`
3. 输出结构化摘要
4. 若状态为 `BRAINSTORM_DRIFT`：建议回到 brainstorm，而非重新运行 impl

## 四种审计状态

| 状态 | 含义 |
|------|------|
| **APPROVED** | Diff 覆盖了 brainstorm 目标与 task 范围，无保留意见 |
| **APPROVED_WITH_NOTES** | 语义正确，但有轻微问题或后续建议 |
| **NEEDS_REWORK** | Diff 与 brainstorm / task 存在语义差距，impl 需重新处理 |
| **BRAINSTORM_DRIFT** | Diff 看似合理，但 brainstorm 本身有误 / 失效 / 与当前代码库脱节 |

## 核心规则

1. **只读** —— review 绝不编辑代码、brainstorm、task 定义或验收条件。
2. **必须读取实际 diff** —— 只看 task 的 DONE 状态不构成审查。
3. **优先使用全新上下文** —— 如有可能，在新会话 / 子代理中执行 review。
4. **范围：brainstorm + task + diff + wiki** —— research 是上游背景，不是审查主要对象。
5. **未经列举检查项不得批准** —— APPROVED 必须至少说明 goal / scope / constraints / diff scope。
6. **BRAINSTORM_DRIFT 退回 brainstorm，而非 impl** —— 上游文档错误时，不能让 impl 背锅。
7. **不自动重复触发** —— 报告一次后即停止。
