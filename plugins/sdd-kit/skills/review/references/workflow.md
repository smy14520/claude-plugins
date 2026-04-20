# Review 工作流：收集 / 判定 / 报告

三个原语的详细流程。SKILL.md 给出高层步骤；本文件给出包含边界情况和多任务审查的完整工作流。

> **范围提醒**：Review 对 impl 产出执行**语义审计**，依据是 spec + diff +（可选）wiki。它绝不修改代码、spec 或任务。唯一的写操作是追加到任务文件的 `## Review log` 部分。

---

## 收集

收齐判定所需的上下文。

### 触发短语

- "review T-003"
- "audit impl"
- "check if this matches spec"
- "cross-check the implementation"
- 显式斜杠命令：`/sdd-kit:review <task-id-or-file>`

### 完整流程

**步骤 1 — 解析目标**

用户输入的形式：

- `T-003`（任务 ID，最常见）
- `.claude/tasks/xhs-webhook.tasks.md`（显式文件路径）
- "the last DONE"（扫描最近的任务文件，查找 DONE/DWC 行）
- `HEAD~1..HEAD`（git 范围，临时审查）

如有歧义（多个文件中出现多条 DONE 行）：列出并提一个澄清问题。

**步骤 2 — 解析 spec**

从任务文件的头部获取（任务文件通常有 `spec: <path>` 前置元数据或显式的 "derived from spec: X" 备注）。

如果是临时任务（无 spec）：退回到**轻量审查**——以用户声明的目标作为 spec 代理，并在审查行中标注轻量化。

完整阅读 `.claude/specs/<name>.md`。重点关注：

- `## Goal`（一句话）
- `## Non-goals`（显式排除项）
- `## Hard constraints`（SLO、速率限制、不变量、安全）
- `## Interface`（公开 API 契约）
- 任何 `## Data / State` 不变量

**步骤 3 — 读取任务条目 + 状态日志**

- 在任务文件中找到特定任务（如 `T-003`）
- 读取其 `deliverable:` 和 `acceptance:` 以明确范围
- 扫描 `## Status log` 中的 DONE/DWC 行——记录时间戳和任何 concerns 块

**步骤 4 — 检查实际 diff**

必须执行。运行：

```bash
git log --oneline --all -- <task's deliverable files>
# 识别属于此任务的提交
git diff <base>..HEAD -- <changed-files>
```

如果不知道基准提交，询问用户：

```
Review 需要 git diff 作为证据。请告诉我:
  a) 这次 task 从哪个 commit 开始？(commit hash / branch)
  b) 或者直接让我看 <branch-A>..<branch-B> 的差异？
  c) 或者 HEAD~N..HEAD 中的 N?
```

**步骤 5 — 可选 wiki 查询**

如果 diff 涉及已有 wiki 覆盖的领域（如 xhs、auth、migrations）：

- 查询 wiki 中的 `[[gotcha-<domain>-*]]` 页面
- 查询 spec 引用的 `[[decision-<topic>]]` 页面

此项为建议性。如果 wiki 为空或与本领域无关，跳过。

**步骤 6 — 组装证据包**

进入判定阶段前，确保已收齐：

- ✅ Spec 文本（目标 / 非目标 / 约束 / 接口）
- ✅ 任务条目（交付物 / 验收标准 / 备注）
- ✅ Impl 状态行（DONE / DWC + 任何 concerns）
- ✅ Git diff（实际代码变更，不仅是文件变更列表）
- ⚪ Wiki 上下文（可选，若跳过需标注）

缺少前 4 项中的任何一项 → 阻断审查，告知用户缺少什么。

---

## 判定

本技能的核心。将 diff 与 spec 仔细比对。

> **强烈建议启用扩展思考**。在整个 sdd-kit 中，这是唯一一个深度推理能物有所值的原语。

### 完整流程

**步骤 1 — 目标覆盖检查**

> diff 是否真正解决了 spec 的一句话目标？

- 阅读 spec 的 `## Goal`
- 指出哪些具体的 diff 块实现了该目标
- 如果无法指出，即为缺口

示例：

```
Spec goal: "小红书 webhook 收到消息后入队列，500ms 内响应 200"
Diff evidence: src/webhooks/xhs-handler.ts:20-40 — handler reads req, pushes to queue, returns 200.
Verdict on goal: ✓ addressed
```

**步骤 2 — 非目标检查**

> diff 是否保持在 spec 显式声明的非目标范围之内？

- 阅读 spec 的 `## Non-goals`
- 扫描 diff 寻找范围蔓延：任务未涉及的文件/功能

示例：

```
Non-goal: "不做消息内容的 NLP 解析，只入队"
Diff evidence: no NLP-related imports, no content parsing code.
Verdict on non-goals: ✓ respected
```

非目标违反通常属于 SPEC_DRIFT 或范围蔓延型 NEEDS_REWORK。

**步骤 3 — 硬约束检查**

> spec 中的硬约束是否在 diff 中有对应证据？

这是审查失败最常见的地方。硬约束通常包括：

- **性能 SLO**（p99 < 200ms，吞吐量 ≥ X/s）
- **速率限制**（每客户端 10/s）
- **安全不变量**（签名验证、HMAC、认证）
- **幂等性保证**
- **重试/退避规则**
- **时钟/时间戳窗口容差**

对每个约束，依次检查：

1. diff 中是否有实现它的代码？（指出 file:line）
2. 是否有能捕获其违反的测试？（指出测试文件）
3. 如果没有：NEEDS_REWORK

约束类型专项检查：

| 约束类型 | 专项检查 |
|---------|---------|
| SLO（延迟） | 是否有零分配快速路径？基准测试？ |
| 速率限制 | 是否有中间件/令牌桶？在 handler 之前应用？ |
| HMAC / 签名 | 是否对原始 body 字节做验证，而非已解析数据？ |
| 幂等性 | 是否有去重键？TTL？存储层？ |
| 重试 | 显式策略（固定/退避）？最大重试次数？ |

**步骤 4 — 接口契约检查**

> 代码是否精确导出了 spec 接口部分所要求的内容？

- Spec：`export function handleXhsWebhook(req: Request): Promise<Response>`
- Diff：搜索匹配的签名

如果 diff 相比 spec 接口有额外/缺失的导出：要么是缺口（NEEDS_REWORK），要么是范围蔓延（APPROVED_WITH_NOTES）。

**步骤 5 — Wiki 陷阱交叉检查**

对每个领域与 diff 重叠的 `[[gotcha-*]]` 页面：

- 阅读该页面的触发条件和修复方案
- 检查 diff 是否处理了该陷阱（如适用）

示例：

```
Wiki: [[xhs-signature-clock-skew]] says "validate ts within 300s window"
Diff: src/webhooks/xhs-verify.ts:15 uses 600s window
Verdict: APPROVED_WITH_NOTES — diff tolerates 2x the documented window; may accept replay attacks slightly longer
```

**步骤 6 — Diff 卫生检查**

即使语义层没问题，也需检查机械性问题：

- 新代码路径未测试（添加了函数但测试未触及）
- 错误路径未处理（try 无 catch，promise 无 .catch）
- 未加注释的魔术数字
- 涉及的文件未列在任务的 `deliverable:` 中（范围蔓延）
- 死导入 / 注释掉的代码
- 本次变更引入的 TODO（而非已有的）

这些通常导致 APPROVED_WITH_NOTES，而非 NEEDS_REWORK——除非缺口出现在关键路径。

**步骤 7 — 分类**

将发现汇总为 [state-machine.md](state-machine.md) 中的一个状态：

| 发现 | 状态 |
|------|------|
| 所有检查通过，无顾虑 | APPROVED |
| 所有检查通过，≥1 个轻微顾虑 | APPROVED_WITH_NOTES |
| 任何硬约束缺口 或 目标未达成 或 必要路径未测试 | NEEDS_REWORK |
| spec 自相矛盾 / 不可行 / 与代码库现状脱节 | SPEC_DRIFT |

### 深度思考提示（启用扩展思考时使用）

按大致以下顺序刻意追问：

1. **"这段实现最隐蔽的错误方式是什么？"** ——强制思考通过测试以外的失败可能。
2. **"如果上线到生产环境，第一个会让我意外的 bug 报告是什么？"** ——暴露边界情况。
3. **"哪个 spec 约束是承重的但在 diff 中不可见？"** ——捕获实现不充分的问题。
4. **"是否存在作者可能不知道的 wiki 陷阱？"** ——将审查与组织记忆耦合。

---

## 报告

分类、记录、总结。

### 完整流程

**步骤 1 — 分类**

按照 [state-machine.md](state-machine.md) 规则，精确选择 APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT 之一。

**步骤 2 — 追加到任务文件的 `## Review log`**

定位或创建 `## Review log` 部分（始终在 `## Status log` 下方）。

每次审查追加一行：

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — <terse summary>
```

完整示例：

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; non-goals respected; rate-limit verified (middleware at src/mw/rate-limit.ts:12); HMAC on raw body; diff clean
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded to 5s (spec said "configurable") src/webhooks/xhs-handler.ts:34; suggest follow-up task
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec §3 requires rate-limit 10/s per client; diff has no rate-limit middleware; acceptance cmd did not exercise burst scenario
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec §4 says "use redis for idempotency"; no redis dependency in package.json, codebase uses in-memory Map; spec predates current arch
```

**步骤 3 — 输出结构化摘要**

向用户输出，严格使用以下格式：

```
## 🔎 Review: T-00X

**State**: <STATE>
**Audited against**: spec `.claude/specs/<name>.md`, diff <base>..HEAD
**Wiki context**: [[gotcha-X]], [[decision-Y]] (or "skipped — no relevant pages")

### Evidence
- Goal:       <verdict + file:line>
- Non-goals:  <verdict>
- Constraints:
  - <constraint>: <verdict + file:line>
  - ...
- Interface:  <verdict>
- Wiki cross-check: <findings or N/A>
- Diff hygiene: <findings or ✓>

### Findings
1. <most important first>
2. ...

### Recommended next step
<one sentence pointing user to impl or spec>
```

**步骤 4 — 按状态给出下一步指引**

| 状态 | 下一步提示 |
|------|-----------|
| APPROVED | "可以合并/发布。若需沉淀经验，运行 `/sdd-kit:wiki` 把 gotcha 或 decision ingest。" |
| APPROVED_WITH_NOTES | "可合并，但建议创建 follow-up task (见 findings)。" |
| NEEDS_REWORK | "回到 `/sdd-kit:impl T-00X`，对照 findings 补齐。不需要重跑 spec。" |
| SPEC_DRIFT | "回到 `/sdd-kit:spec <name>` 调整 spec。impl 不应在错误前提下反复跑。" |

**步骤 5 — 不要自动推进**

审查报告一次后即停止。即使是 APPROVED，也不要自动提议"转到下一个任务"——这是用户的决定。

### 边界情况

**情况：impl 有多条状态行（多次运行）**

审查针对最新的 DONE / DONE_WITH_CONCERNS 行。更早的 NEEDS_CONTEXT / BLOCKED 行属于审计痕迹的一部分，但不是审计目标。

**情况：用户要求审查仍处于 NEEDS_CONTEXT 或 BLOCKED 状态的任务**

拒绝：

```
T-00X 当前状态是 <STATE>，尚未 DONE。先完成 impl 再 review。
```

**情况：用户在 NEEDS_REWORK → DONE 循环后要求复审**

执行全新审查。追加新的审查行。不要编辑之前的 NEEDS_REWORK 行（保留审计痕迹）。

**情况：任务是临时的（无 spec）**

轻量模式：

- 以用户声明的目标作为 spec 代理（不明显时需显式询问）
- 跳过约束/接口检查（无对照依据）
- 聚焦于 diff 卫生 + wiki 交叉检查
- 在审查行中标注：`note: ad-hoc, lightweight review`

**情况：diff 巨大（>500 行，涉及 10+ 文件）**

不要静默略读。要么：

- 询问用户聚焦哪个子系统，或者
- 报告 NEEDS_REWORK，附带发现："task scope appears oversized; consider re-decomposition"

**情况：spec 为空或仅为占位**

立即标记 SPEC_DRIFT：

```
spec 缺少可审计的 goal / non-goals / constraints。无法对 impl 做语义审计。
建议回到 /sdd-kit:spec 补齐 spec 内容契约 (content-contract)。
```

---

## 多任务/批量审查

如果用户说"审查整个任务文件"：

- 按顺序审查每个 DONE/DWC 任务
- 每个任务输出一条审查行
- 最终摘要："Reviewed N tasks: K APPROVED, L APPROVED_WITH_NOTES, M NEEDS_REWORK, P SPEC_DRIFT"
- 遇到第一个 SPEC_DRIFT 即停止（退回 spec 会使后续审查无效）

---

## 新上下文建议

**最佳实践**：在新聊天/子代理中调用 `/sdd-kit:review`，而非运行过 impl 的同一会话。原因：

- 编写代码的上下文已锚定在"这是正确答案"上
- 新上下文迫使以未受污染的视角重新阅读 spec 和 diff
- 模拟人类代码审查的工作方式（不同审查者，不同假设）

如果无法避免同会话审查，在审查行中标注：

```
note: same-session review (self-audit); consider second opinion
```
