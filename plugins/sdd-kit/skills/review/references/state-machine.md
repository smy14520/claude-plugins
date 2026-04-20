# 四态审查状态机

审查报告且仅报告以下四种状态之一。本文件给出定义、退出标准和转换规则。

> **与 impl 的状态机平行**，但维度不同。Impl 衡量"任务验收是否通过"。Review 衡量"diff 是否在语义上满足 spec"。

---

## APPROVED

**含义**：diff 实现了 spec 的目标，遵守了非目标，满足硬约束，匹配接口契约。无保留意见。

### 退出标准（必须全部满足）

- 目标覆盖：能指出实现目标的 diff 块
- 非目标：diff 未涉足显式排除的范围
- 硬约束：每个约束在 diff 中有证据（代码或测试）
- 接口契约：导出与 spec 一致
- Wiki 交叉检查：无相关陷阱被违反（或无适用的陷阱）
- Diff 卫生：无未测试的必要路径、无错误路径缺口、无范围蔓延

### 禁止用于声称 APPROVED 的理由

- "验收命令通过了，看起来不错" → 那是 impl 的 SelfCheck，不是 review
- "我扫了一眼 diff，感觉没问题" → 必须引用 file:line 证据
- "该领域没有 gotcha 页面" → 可以跳过 wiki，但必须显式说明

### 审查行示例

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — goal met; non-goals ✓; rate-limit mw ✓ (src/mw/rate-limit.ts:12); HMAC on raw body ✓; diff clean
```

---

## APPROVED_WITH_NOTES

**含义**：语义层正确，但审查者标记了非阻断性的轻微问题。

### 适用场景

- 轻微的范围蔓延但无害（如同一次提交中修复了不相关的拼写错误）
- 硬编码值而 spec 暗示应可配置（软约束）
- 非关键路径缺少可选的测试覆盖
- Wiki 陷阱部分处理但未完全处理
- 命名/风格略微偏离项目惯例

### 必要输出

必须包含一个 concerns 块，说明：

- 问题是什么（每条一句话）
- 所在位置（file:line）
- 严重性论证（为什么是轻微的，而非阻断性的）
- 可选：建议的后续任务

### 禁止事项

- 用 APPROVED_WITH_NOTES 掩盖真正的硬约束缺口：那应该是 NEEDS_REWORK
- 模糊的问题描述（"可以更整洁"）而无具体内容
- 堆叠 5+ 个轻微问题而不自问"这实际上应该是 NEEDS_REWORK 吗？"

### 审查行示例

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded 5s (spec said "configurable") src/webhooks/xhs-handler.ts:34; suggest follow-up
```

### 后续任务模式

对于实质性问题，建议一个后续任务：

```
建议新建 T-0NN: "Make xhs webhook timeout configurable via env"
  role: backend
  depends-on: [T-004]
  estimate: 30min
```

由用户决定是否创建。

---

## NEEDS_REWORK

**含义**：diff 与 spec 之间存在语义缺口。Impl 必须重新处理。

### 适用场景

- 硬约束缺口（缺少速率限制、SLO 未处理、安全检查缺失）
- Spec 目标未完全交付（如 handler 对 95% 返回 500ms，但 spec 要求 99%）
- 非目标被违反（范围蔓延到排除的领域）
- 必要路径无测试覆盖
- 接口契约不匹配（导出错误、签名不同）
- Wiki 陷阱被直接违反且无合理解释

### 必要输出

必须指定：

- **缺口**：一句话概述缺失或错误的内容
- **证据**：指向展示缺口的代码的 file:line（或"无代码处理此问题"）
- **Spec 引用**：未满足的 spec 章节/约束
- **建议修复方向**：提示而非处方（审查者不是 impl）
- **影响范围**：是否需要重新拆分任务，还是局部修补即可？

### 禁止事项

- 用 NEEDS_REWORK 强加个人品味（"我会用 X 方式做"）
- 对 spec 未要求的内容声称 NEEDS_REWORK
- 要求超出修补缺口所需的重构
- 在审查中写出实际修复代码（那是 impl 的下一个循环）

### 审查行示例

```
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec §3 requires rate-limit 10/s per client; diff has no rate-limit middleware (scanned src/webhooks/ and src/mw/); acceptance cmd did not exercise burst scenario
```

### 解决路径

用户选项：

1. 带上审查发现作为上下文重新运行 `/sdd-kit:impl T-00X`
2. 如果缺口太大无法在一个循环内解决，重新拆分任务
3. 如果缺口揭示该功能应推迟，放弃该任务

---

## SPEC_DRIFT

**含义**：diff 看起来合理，但 spec 本身是错误的、不一致的或不可行的。退回 spec skill，而非 impl。

### 适用场景

- Spec 要求了代码库中不存在的依赖
- Spec 的硬约束在物理上不可行（如对网络调用要求 p99 < 1ms）
- Spec 自相矛盾（§2 说 X，§4 说非 X）
- Spec 假设的架构已不再适用（过时的 spec vs 当前代码）
- Spec 的验收命令引用了已废弃的基础设施
- Research 阶段被跳过，spec 中的猜测被现实推翻

### 必要输出

必须指定：

- **偏差**：一句话概述 spec 错在哪里
- **证据**：引用有问题的 spec 行 + 指向代码库现状
- **影响**：impl 的哪些部分仍然有效，哪些需要重新考虑
- **建议路径**：需要修改 spec 的哪个章节；是否需要 research

### 禁止事项

- 用 SPEC_DRIFT 作为 impl 实际有错时的逃避出口（那应该是 NEEDS_REWORK）
- 对 spec 歧义声称 SPEC_DRIFT（歧义 → impl 应发出 NEEDS_CONTEXT；如果 impl 猜测了，那是 impl 的 NEEDS_REWORK）
- SPEC_DRIFT 仅说"spec 可以更清晰"——必须引用具体的矛盾或不可行之处

### 审查行示例

```
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec §4 requires redis for idempotency; no redis dep in package.json; codebase uses in-memory Map in src/store/dedup.ts; spec predates architecture change
```

### 恢复路径

用户选项：

1. `/sdd-kit:spec <name>` 修订偏差的章节
2. `/sdd-kit:research <topic>` 如果偏差揭示了知识缺口
3. 如果 impl 的部分工作对修订后的 spec 仍然可用，保留之
4. 如果 spec 的前提从根本上就是错的，完全放弃此任务

**不要先重新运行 impl。** 基于错误 spec 的 impl 只会重新制造 bug。

---

## 状态转换规则

### 正向转换（允许）

```
impl (DONE / DONE_WITH_CONCERNS)  ──►  收集  ──►  判定  ──►  APPROVED
                                                       │
                                                       ├──►  APPROVED_WITH_NOTES (+ concerns block)
                                                       │
                                                       ├──►  NEEDS_REWORK (+ gap block)  ──►  back to impl
                                                       │
                                                       └──►  SPEC_DRIFT (+ drift block)  ──►  back to spec
```

### 返工复审

```
NEEDS_REWORK  ──(impl 重新运行，报告 DONE)──►  新审查循环，追加新审查行
SPEC_DRIFT    ──(spec 修订，任务可能重新拆分，impl 重新运行)──►  新审查循环
APPROVED      ──(默认无操作)──►  保持 APPROVED
APPROVED_WITH_NOTES  ──(后续任务已创建)──►  保持 APPROVED_WITH_NOTES（原始记录）
```

### 禁止的转换（硬性规则）

- ❌ `APPROVED ← NEEDS_REWORK` 静默转换（绝不允许"再想想，够好了"而不重新审查证据）
- ❌ `APPROVED ← SPEC_DRIFT` 静默转换（spec 偏差不会因忽略而消失）
- ❌ `APPROVED_WITH_NOTES` 带 5+ 个问题（此时应重新归类为 NEEDS_REWORK）
- ❌ 编辑之前的审查行（只追加；每次复审新起一行）

每次重新进入审查都追加一条新的审查行；旧行保留用于审计。

---

## 同一任务的多条审查行

一个任务可能在多次复审中积累多条审查行：

```
- [✗] T-003 (NEEDS_REWORK) — 2025-04-18 17:10 — rate-limit missing
- [✓] T-003 (APPROVED) — 2025-04-18 18:40 — re-reviewed after impl rework, rate-limit now at src/mw/rate-limit.ts:12
```

这就是审计痕迹。不要合并为一行。

---

## 与 impl 状态机的关系

Review 和 impl 拥有正交的状态机。一个任务可以是：

| Impl 状态 | Review 状态 | 含义 |
|-----------|------------|------|
| DONE | 未审查 | impl 完成，等待审计 |
| DONE | APPROVED | 可发布 |
| DONE | APPROVED_WITH_NOTES | 可发布，有轻微后续事项 |
| DONE | NEEDS_REWORK | impl 认为完成了；审查不同意 → 回到 impl |
| DONE | SPEC_DRIFT | impl 做了它该做的；spec 有错 → 回到 spec |
| DONE_WITH_CONCERNS | APPROVED | 顾虑被审查者接受 |
| DONE_WITH_CONCERNS | NEEDS_REWORK | 顾虑未被接受 |
| NEEDS_CONTEXT | （无法审查） | impl 未完成 |
| BLOCKED | （无法审查） | impl 未完成 |

---

## 升级规则

如果一个任务已循环 `NEEDS_REWORK → impl → NEEDS_REWORK` 3 次以上：

```
⚠️ T-003 has entered NEEDS_REWORK 3 times in review.
Suggestion:
  - Task may be mis-scoped (re-decompose via /sdd-kit:task)
  - Or spec may be under-specified (return to /sdd-kit:spec with findings as feedback)
  - Or review criteria may be too strict for task's actual scope (reconcile with user)

Do not keep cycling review → impl → review without addressing the upstream.
```
