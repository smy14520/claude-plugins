# 四状态机

Impl 报告且仅报告以下四种状态之一。本文件给出定义、退出标准和转换规则。

---

## DONE

**含义**：任务完成。所有验收标准通过。无已知妥协或遗留问题。

### 退出标准（全部必须满足）

- `acceptance:` 中的每条命令均已执行并返回成功
- `acceptance:` 中的每个文件状态谓词均已验证
- 无已知偏离 spec 或任务约束的情况
- 代码自洽（本任务无残留的 TODO）

### 禁止声称 DONE 的理由

- "Acceptance 在本地通过了" → 你是否真的运行了全部？包括那条 HTTP 的？
- "差不多够了" → 应标记为 DONE_WITH_CONCERNS
- "除了测试，测试我稍后补" → 不是 DONE
- "在脑子里验证过了" → 命令实际运行之前不是 DONE

### 状态行示例

```
- [x] T-003 (DONE) — 2025-04-18 14:20 — 3/3 acceptance green
```

---

## DONE_WITH_CONCERNS

**含义**：验收通过，但执行者做了一项值得上报的妥协。

### 何时使用

- 使用了满足验收但并非最干净方案的变通手段
- 跳过了任务备注中提到的可选改进
- 引入了未来读者应知晓的小额技术债
- 以次要方式偏离了项目约定（已在代码内注明）

### 必须输出

必须包含 concerns 块，写明：

- 妥协是什么（一句话）
- 它在代码中的位置（file:line）
- 建议的后续行动（可选：建议新 task ID）

### 禁止事项

- 用 DONE_WITH_CONCERNS 掩盖真正的失败：那应该是 BLOCKED 或 NEEDS_CONTEXT
- "Concerns: 代码可以更干净" 而无具体内容（不可执行）

### 状态行示例

```
- [?] T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:50 — passed but retry uses fixed 3 tries, no backoff; src/webhooks/xhs-handler.ts:42
```

### 后续模式

对于实质性 concern，建议一个后续任务：

```
建议新建 T-0NN: "Add exponential backoff to xhs retry"
  role: backend
  depends-on: [T-003]
  estimate: 1h
```

由用户决定是否创建。

---

## NEEDS_CONTEXT

**含义**：执行者遇到歧义或信息缺失，被迫做出设计决策。拒绝猜测。

### 何时使用

- Spec 说 X，task 说 Y，二者矛盾
- Acceptance 引用了不存在的文件/命令
- 缺少影响行为的具体值（例如 TTL、重试次数、URL、枚举选择）
- 存在两种合理实现方案且任务未做选择
- 必需的上游依赖行为未定义
- 任务交付物使用了开放性动词（`校准 / 保持 / 验证 / 确保 / 适配`）而非带有具体目标的 `CREATE / ADD / SET / DELETE / REPLACE`——不要自行研究缺失的值
- 任务或 spec 文件中包含与本任务相关的未解决 `<TODO-DECIDE>` 或 `<TBD>` 标记——spec 尚未定稿

### 必须输出

必须指定：

- **受阻于**：一句话概述歧义所在
- **所需信息**：能解除阻塞的具体问题
- **歧义来源**：歧义位于 spec / task 的何处
- **建议解决方案**：对 spec 或 task 做什么变更可解除阻塞
- **代码状态**："no code changes committed" 或 "partial: <已提交的内容>"

### 禁止事项

- 用 NEEDS_CONTEXT 来逃避仔细阅读 spec
- 对 spec 中已做决策的问题声称 NEEDS_CONTEXT（重新阅读，不要询问）
- 静默做出选择后标记 DONE——这是需要避免的核心失败模式
- 自行开展研究（阅读外部文档、网络搜索、探索代码库以确定"这个 URL 应该是什么"）来解决开放性动词或未解决标记——那是 spec / research 阶段的工作，不是 impl 的。发出 NEEDS_CONTEXT 并退回。

### 状态行示例

```
- [!] T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10 — spec ambiguous on replay window: 24h vs 7d? acceptance says 24h, spec says 'align with wechat'
```

### 解决路径

用户选项：

1. 会话中澄清 → impl 消化澄清内容，重新运行任务
2. 更新 spec → 重新定稿 spec，必要时重新分解，重新运行 impl
3. 删除/缩减任务 → 标记任务 `status: dropped`
4. 推迟 → 保持 NEEDS_CONTEXT，稍后回来

---

## BLOCKED

**含义**：环境或外部因素阻止任务执行，与设计歧义无关。

### 何时使用

- 依赖未安装，缺少二进制文件
- 外部服务不可达（数据库、API、队列）
- Migration 因基础设施原因失败（版本不匹配、缺少扩展）
- 机器级别的权限/认证问题
- 上游任务仍为 `NEEDS_CONTEXT` 或 `BLOCKED`（本任务无法继续）

### 必须输出

必须指定：

- **阻塞项**：一句话概述
- **症状**：确切的错误信息
- **已尝试**：已执行的恢复步骤
- **解除路径**：需要什么外部操作（谁/什么）
- **代码状态**："no code changes committed" 或 "partial: <已提交的内容>"

### 禁止事项

- 用 BLOCKED 来逃避 SelfCheck（如果你没有运行命令，你不知道它是被阻塞的）
- 静默使用绕过阻塞的变通方案（最多是 DONE_WITH_CONCERNS，但更可能是 NEEDS_CONTEXT）
- 对设计问题声称 BLOCKED（那应该是 NEEDS_CONTEXT）

### 状态行示例

```
- [✗] T-003 (BLOCKED) — 2025-04-18 15:30 — postgres 14 vs 15 schema mismatch; migration requires 15; local is 14
```

### 恢复路径

用户选项：

1. 修复环境 → 重新运行任务
2. 改写为适应当前环境（新决策：重新运行 spec / task）
3. 推迟任务，跳到其他可执行任务
4. 删除任务

---

## 状态转换规则

### 正向转换（允许）

```
(start)  ───────►  Execute  ───────►  SelfCheck  ────►  DONE
                      │                 │
                      │                 ├──► DONE_WITH_CONCERNS (+ concerns doc)
                      │                 │
                      │                 └──► BLOCKED (acceptance cmd fails for env reason)
                      │
                      ├────────────►  NEEDS_CONTEXT (ambiguity found)
                      │
                      └────────────►  BLOCKED (env issue during execute)
```

### 返工转换（重新打开）

```
NEEDS_CONTEXT  ──(user clarifies)──►  re-Execute
BLOCKED        ──(env fixed)──────►  re-Execute
DONE_WITH_CONCERNS  ──(follow-up filed)──►  stays DONE_WITH_CONCERNS
DONE           ──(regression found)──►  file NEW task, do NOT revise T-003
```

### 禁止的转换（硬性规则）

- ❌ `DONE ← BLOCKED` 静默转换（绝不允许"想出了变通方案，现在 DONE 了"而不经过显式的重新 SelfCheck）
- ❌ `DONE ← NEEDS_CONTEXT` 静默转换（绝不允许"猜了个答案就继续了"）
- ❌ `DONE ← DONE_WITH_CONCERNS`（concerns 不会自动消失；它们需要后续跟进）

每次重新进入任务时追加一条新的状态行；旧行保留用于审计。

---

## 每个任务的多条状态行

一个任务可能在多次运行中积累多条状态行：

```
- [!] T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10 — replay window ambiguity
- [✗] T-003 (BLOCKED) — 2025-04-18 15:40 — fixed ambiguity, now postgres version issue
- [x] T-003 (DONE) — 2025-04-18 16:30 — env fixed, 3/3 acceptance green
```

这就是审计轨迹。不要合并为一行。

---

## 升级规则

如果一个任务已经循环经历 NEEDS_CONTEXT 或 BLOCKED 3 次以上：

```
⚠️ T-003 has entered NEEDS_CONTEXT/BLOCKED 3 times.
Suggestion:
  - The task may be mis-scoped (re-decompose via task skill)
  - Or the spec may have a deeper ambiguity (return to spec skill)
  - Or the environment fundamentally doesn't fit the design (return to research)

Do not keep retrying without addressing the upstream.
```
