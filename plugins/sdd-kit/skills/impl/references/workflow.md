# Impl 工作流：Pick / Execute / SelfCheck / Report

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出完整工作流，包括边界情况和 ad-hoc 模式。

> **范围提醒**：Impl 的 `SelfCheck` 只运行任务自身的 `acceptance:` 命令。它不对 spec 做语义审计——那是 `review` skill 的职责。将二者分开，可以避免 impl 在仅看 task 的有限上下文下，默默批准偏离 spec 的工作成果。

---

## Pick

选择要执行的任务。

### 触发短语

- "实施 T-003"（指定 task ID）
- "执行下一个 task"
- "run next task for spec X"
- "start impl on <task-file>"

### 完整流程

**步骤 1 — 定位 task 文件**

情况 A：用户指定了文件 → 直接使用
情况 B：用户指定了 spec → 查找 `.claude/tasks/<spec>.tasks.md`
情况 C：都未指定 → 列出最近的 task 文件：

```bash
ls -t .claude/tasks/*.tasks.md | head -5
```

询问："找到以下 task 文件，选哪个？" 或直接取最近的并请求确认。

情况 D：不存在 task 文件 → 进入 **ad-hoc 模式**（见下文）。

**步骤 2 — 读取任务列表 + 状态日志**

从 `## Status log` 区域解析所有任务及其当前状态。

将每个任务分类为：

- **Pending** — 尚无状态行
- **DONE** — 最后状态为 DONE（不可重新执行）
- **DONE_WITH_CONCERNS** — 最后状态为 DWC（用户要求时可重新执行）
- **NEEDS_CONTEXT** / **BLOCKED** — 等待外部解决
- **Dropped** — 任务块中标记 `status: dropped`

**步骤 3 — 查找可执行任务**

可执行 = Pending + 所有 `depends-on` ID 的状态为 DONE 或 DONE_WITH_CONCERNS。

如果用户指定了具体 ID → 确认可执行性；若其依赖不完整，输出：

```
⚠️ T-003 depends on T-001, T-002. 当前状态: T-001=DONE, T-002=NEEDS_CONTEXT.
建议先解决 T-002，或明确你要 (a) 强制执行 T-003, (b) 切到 T-002, (c) 取消。
```

如果用户说"下一个" → 选择编号最小的可执行任务。执行前确认：

```
下一个: T-003 `<title>`
  Role: backend
  Deliverable: src/webhooks/xhs-handler.ts
  Estimate: 3h
  Depends-on: T-001 (DONE), T-002 (DONE)

开始？(y/n/选其他)
```

**步骤 4 — 读取 spec（可选上下文）**

如果任务引用了 spec（task 文件前置数据中的 `spec: <name>`），读取一次 spec 作为上下文。不要从 spec 中重新推导已在任务的 acceptance / notes 中存在的内容。

### 边界情况

**情况：所有任务已完成**

输出："所有任务已完成 (N/N DONE). 建议 lint spec 与代码一致性，或关闭此 task file。"

**情况：task 文件存在循环依赖**

阻止："依赖环检测到 T-00X → T-00Y → T-00X. 这是 task-phase 问题，不是 impl 能解决的。请返回 task skill 修复。"

**情况：用户想重新执行已 DONE 的任务**

询问："T-003 已 DONE on <date>. 原因？(a) 代码被改动, (b) acceptance 需重跑, (c) 其他". 仅在用户明确后继续。

### Ad-hoc 模式（无 task 文件）

用户说"实现 X"但没有 task 文件。

**步骤 A1 — 确认范围**

询问：

```
没有 task 文件。进入 ad-hoc 模式。请确认:
  1. Deliverable (文件/模块/端点)?
  2. Acceptance (怎么算 DONE?命令/行为?)
  3. 是否先写一个 minimal tasks file (1 个任务) 再执行？
```

等待回答。如果用户希望创建最小 task 文件 → 调用 task skill 生成包含 1 个任务的种子。

**步骤 A2 — 同样的执行流程**

否则，将用户的回答视为任务。创建具有相同字段的内存任务对象。正常运行 Execute → SelfCheck → Report。

**步骤 A3 — 状态记录在哪里？**

没有 task 文件时，状态写入：

- 用户可见的摘要（必须）
- `.claude/impl-logs/<name>.log.md`，仅在用户需要持久追踪时（可选，按需创建）

---

## Execute

编写代码。

### 完整流程

**步骤 1 — 读取 deliverable + acceptance + notes**

将目标状态记入脑中：

- 哪些文件会变更
- 必须满足哪些验收标准
- 任何关于非显而易见上下文的备注

**步骤 2 — 规划最小差异**

思维模型："能让所有验收标准通过的最小变更"。不做推测性添加，不做相邻重构。

**步骤 3 — 执行编辑**

优先使用最小化的聚焦编辑。遵循现有风格。不主动添加注释。对齐项目约定（阅读附近代码了解风格）。

**步骤 4 — 处理歧义**

如果在 Execute 过程中的任何时候发现：

- Spec 说 X 但 task 说 Y → 停止。NEEDS_CONTEXT："spec 和 task 冲突 on <point>"
- Acceptance 提到了不存在的文件/命令 → 停止。NEEDS_CONTEXT："acceptance 引用了 <path>，但不存在"
- 需要做设计选择（例如"缓存键应该包含 user_id 吗？"）→ 停止。NEEDS_CONTEXT："需要决策: <question>"

不要尝试变通方案。发出 NEEDS_CONTEXT 状态并交还控制权。

**步骤 5 — 处理阻塞**

如果环境阻碍了进度（依赖未安装、服务未运行、migration 无法应用）：

- 尝试一种合理的恢复操作（例如安装缺失的依赖）
- 如果恢复失败或需要外部操作 → 停止。BLOCKED："<阻塞描述>"

### 什么算作设计决策（触发 NEEDS_CONTEXT）

- 在 spec 给出选项时选择算法
- 选择未指定的命名/路径/表列名
- 决定是否实现"大概率隐含"的功能 A
- 在 spec 未指定时决定重试次数/超时时间

### 什么不算设计决策（静默执行）

- 选择局部变量名
- 选择内部辅助函数结构
- 选择私有导入顺序
- linter 会自动标准化的格式决策

判断标准：审查者会合理地指出你的选择吗？如果是 → 询问 / NEEDS_CONTEXT。

---

## SelfCheck

运行任务的验收命令。报告事实，而非感觉。这是**自我**检查（运行自己的 acceptance），不是语义审查（那是 `review` skill 的职责）。

**SelfCheck 不用于**：

- 判断代码是否真正解决了用户层面的问题（review）
- 将实现与 spec 约束进行比较（review）
- 查阅 wiki 了解相关注意事项（review）
- 查看超出当前任务文件范围的 git diff（review）

**SelfCheck 用于**：

- 运行任务中的每一条 `acceptance:` 命令
- 仔细读取其退出码和输出
- 在任何验收失败时拒绝声称 DONE

### 完整流程

**步骤 1 — 解析 acceptance 块**

从 `acceptance:` 字段中提取每条命令或谓词。

**步骤 2 — 按顺序运行**

命令：带超时执行。捕获退出码 + 最后约 40 行输出。

文件状态谓词：读取文件，根据 acceptance 检查导出的签名/内容。

HTTP 谓词：运行 curl 或等效命令，解析响应。

**步骤 3 — 收集结果**

```
acceptance 1/3: `pnpm test tests/webhooks/xhs.test.ts` → exit 0 ✅
acceptance 2/3: file src/webhooks/xhs-handler.ts exports handleXhsWebhook(req) → ✅
acceptance 3/3: `curl -X POST localhost:3000/webhook/xhs ...` → HTTP 200 ✅
```

**步骤 4 — 决定状态**

全部通过 + Execute 过程中无顾虑 → **DONE**
全部通过 + 有已记录的顾虑（妥协、技术债、非理想方案）→ **DONE_WITH_CONCERNS**
有任何失败且失败与 acceptance 相关 → 报告为 **BLOCKED**（若是歧义则为 NEEDS_CONTEXT）

### 边界情况

**情况：acceptance 是人工检查**

如果某条验收标准需要人眼确认（例如"UI 看起来正确"）：

- 运行自动化部分
- 对人工部分：发出"DONE-PENDING-MANUAL: <criterion> — 请人工确认后在 status log 改 [x]"

**情况：acceptance 命令本身有问题**

如果 `pnpm test path/xxx.test.ts` 因工具链问题失败（不是被测代码的问题）：

- BLOCKED："toolchain error <detail>, cannot SelfCheck"
- 不要将工具链故障解读为代码故障

**情况：acceptance 通过但其他测试中断**

如果运行 `pnpm test`（范围大于任务的 acceptance）发现无关的故障：

- 报告本任务 DONE（acceptance 已通过）
- 在状态行中注明："note: pnpm test (broader) shows N pre-existing failures in <area>"
- 提醒用户："此任务 DONE, 但观察到项目整体测试有问题。单独开任务还是忽略？"

---

## Report

将状态行追加到 task 文件 + 输出结构化摘要。

### 完整流程

**步骤 1 — 写入状态行**

按 SKILL.md 格式。追加到 task 文件的 `## Status log` 区域。

不要编辑 task 文件的其他部分。

**步骤 2 — 向用户输出摘要**

```
✅ T-003 (DONE) — 2025-04-18 14:20

Deliverable: src/webhooks/xhs-handler.ts (+42 lines)
Verified:
  ✅ pnpm test tests/webhooks/xhs.test.ts (3/3 pass)
  ✅ file exports signature match
  ✅ curl smoke 200

Remaining tasks: 4
Next eligible: T-004, T-005

继续下一个？(说 "continue" / "do T-00X" / 或停下做别的)
```

对于 DONE_WITH_CONCERNS，添加 concerns 块：

```
⚠️ T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:50

Concerns:
  - retry logic uses fixed 3 tries, no exponential backoff (spec said "retry", not "backoff")
  - skipped input fuzzing (not in acceptance)
Recommendation: 回头可以 follow-up task T-0NN 加 backoff
```

对于 NEEDS_CONTEXT：

```
🟡 T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10

Blocked at: ambiguity on replay window duration
Needed: 24h or 7d?
Source of ambiguity: spec §Constraints "idempotent" without TTL; task acceptance says "24h" but comment says "align with wechat (7d)"
Suggested resolution: return to spec, add explicit TTL
No code changes committed.
```

对于 BLOCKED：

```
🔴 T-003 (BLOCKED) — 2025-04-18 15:30

Blocker: postgres version mismatch
  local: postgres 14.x
  expected: postgres 15.x (migration uses 15-only syntax)
Tried: `brew install postgres@15` — needs sudo / user action
No code changes committed.
Unblock path: align postgres version or rewrite migration for 14 compat (decision needed).
```

**步骤 3 — 多任务运行时更新 impl-log**

如果用户在同一会话中运行多个任务，维护 `.claude/impl-logs/<name>.log.md`：

```markdown
## [2025-04-18 14:20] T-003 DONE
- deliverable: src/webhooks/xhs-handler.ts
- selfcheck: 3/3 pass
- duration: 2h 40min

## [2025-04-18 15:10] T-005 NEEDS_CONTEXT
- blocked at: replay window ambiguity
- duration: 0h 20min
```

单任务运行不需要 impl-log；摘要即可。

**步骤 4 — Wiki 摄入建议（条件触发）**

**触发条件**：状态为 `DONE_WITH_CONCERNS` 或 `BLOCKED`。`DONE` 永不触发（无内容可摄入）。`NEEDS_CONTEXT` 永不触发（任务未完成——提取知识为时过早）。

**决定建议的页面类型**：

| 状态 | 建议类型 | 页面名称模式 |
|------|----------|-------------|
| `DONE_WITH_CONCERNS` 且有具体妥协 | `gotcha` | `<domain>-<scenario>`（例如 `xhs-signature-clock-skew`） |
| `DONE_WITH_CONCERNS` 因设计权衡 | `decision` | `<choice>-for-<domain>`（例如 `fixed-retry-vs-backoff-for-xhs`） |
| `BLOCKED` 因环境不匹配 | `gotcha` | `<tool>-<version-issue>`（例如 `postgres-14-vs-15-migration`） |
| `BLOCKED` 因上游依赖未解决 | （不提建议——这不是知识，是流程） | — |

**输出格式**（追加到 Report 摘要块）：

```
💡 Knowledge worth ingesting (you decide; nothing saved until you run /sdd-kit:wiki):

   Suggested page: [[xhs-signature-clock-skew]]
   Type: gotcha
   Draft:
     ## Trigger
     Local-to-server clock drift > 5 min causes HMAC timestamp mismatch.
     ## Symptoms
     XHS webhook returns 401 "signature expired".
     ## Root cause
     Server validates ts within 300s window; our NTP sync was stale.
     ## Fix
     Added chrony to dev env; task T-003 status line file:line.

   Command to ingest:
     /sdd-kit:wiki ingest gotcha xhs-signature-clock-skew
```

**规则**：

1. **绝不自动摄入。** 命令行供用户复制粘贴，impl 不应执行它。
2. **草稿必须具体。** 不使用"[描述问题]"之类的通用占位符。从实际的 concern/blocker 文本中填写。
3. **引用任务。** 在草稿中包含 `task: T-00X` 和相关 `file:line` 指针，以便 wiki 页面可追溯到任务。
4. **若 BLOCKED 纯属流程问题则跳过。** 例如"等待 T-001 NEEDS_CONTEXT"不是知识，不要建议页面。
5. **每次任务运行建议一次。** 如果 impl 重新运行同一任务且状态仍为 DWC/BLOCKED，仍然每次都包含建议（用户可能已摄入——没关系，wiki ingest 会检测冲突）。

**设计理由**（简版）：

- DONE_WITH_CONCERNS 捕获了最有价值的隐性知识——"能用，但这是我们妥协的地方"。不捕获就是浪费。
- 因环境不匹配导致的 BLOCKED 是一种重复痛点模式，wiki 的 gotcha 页面类型正是为此设计的。
- 保持为建议（而非自动摄入）遵循了"可控优先"原则——用户始终掌握什么成为持久知识的决定权。

**步骤 5 — 不要自动推进**

在一个任务的 Report 之后始终停止。用户说"continue"才继续。

### 边界情况

**情况：用户预先说了"run all tasks"**

允许，但：

- 仍然按任务报告状态
- 在第一个 NEEDS_CONTEXT 或 BLOCKED 处停止（不跳过）
- 结尾摘要："Ran N tasks, M DONE, K with concerns, stopped at T-00X (state)"

**情况：同一 concern 反复出现摄入建议**

如果任务循环经历 DONE_WITH_CONCERNS → 返工 → DONE_WITH_CONCERNS（同一 concern），仍然每次发出建议。Wiki ingest 自身会处理去重（按 `references/operations.md#ingest` 步骤 3 的 page-exists 提示）。
