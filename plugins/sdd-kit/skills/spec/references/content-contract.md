# Spec 内容契约

Spec 是一份可靠的设计契约。本文件精确定义了 spec 中应包含和不应包含的内容。

## 必需章节

一份合法的 spec 必须包含以下全部章节：

### 1. Frontmatter

```yaml
---
status: draft | accepted | revising | superseded
date: YYYY-MM-DD
tags: [<domain>, ...]          # optional
supersedes: <old-spec-name>    # optional
---
```

### 2. `# <Feature>` — 标题

Kebab-case 格式的主题名，与文件名一致。

### 3. `## Goal` — 一句话

祈使语气。描述结果，而非过程。

- ✅ "Provide an idempotent webhook endpoint for xhs customer events."
- ❌ "Implement xhs webhook integration with retry logic and signature verification."
- ❌ "Improve webhook handling."

### 4. `## Non-goals` — 至少 2 条明确排除项

本 spec 不涉及的内容。防止范围蔓延。

- ✅ "Does NOT cover outbound xhs-to-customer messaging."
- ✅ "Does NOT migrate existing wechat webhook handler (separate spec)."
- ❌ （缺少 non-goals）—— spec 必然会范围蔓延

### 5. `## Hard constraints`

尽可能使用数值或二元判定：

- 延迟：p99 < 200ms
- 吞吐量：500 req/s 持续负载
- 一致性：至少一次投递，按 `event_id` 幂等
- 安全性：签名验证通过；时钟偏移容忍 ≤ 5 min
- 兼容性：不得破坏现有 `/webhook/wechat` handler

禁止出现没有数值支撑的模糊形容词（"fast"、"reliable"、"scalable"）。

### 6. `## Interface contract`

精确的输入、输出、错误结构：

- HTTP：方法、路径、请求体 schema、响应体 schema、状态码
- 函数：签名、参数类型、返回类型、异常
- 事件：topic、payload schema、确认协议
- 配置 / 常量：精确名称和精确值（URL、枚举列表、SLO 数字、feature-flag 键名）

**未确定的具象值**（一个你尚不知道的 URL、一个你尚未决定的枚举）必须写为 `<TODO-DECIDE: 具体问题>`。诸如"与 docs 保持一致" / "校准 XX" / "保持默认"之类的描述禁止替代精确值——它们会将未解决的工作静默泄漏到 task 和 impl 阶段，而届时解决成本更高。另见 Finalize 步骤的标记扫描。

包含验收标准块：

```markdown
### Acceptance
- [ ] POST /webhook/xhs returns 200 within 200ms for valid signed request
- [ ] Returns 401 for invalid signature
- [ ] Returns 409 for replay (duplicate event_id within 24h)
- [ ] Metrics emit: counter `webhook.xhs.received`, histogram `webhook.xhs.latency`
```

### 7. `## Data / state design`

涉及的实体、表、队列、缓存。如有状态转换也需说明。

- 涉及的表：`xhs_events (id, event_id, payload, processed_at)`
- 缓存键：`xhs:replay:<event_id>` TTL 24h
- 状态机：`pending → processed | failed`

禁止编写完整的 schema DDL（那属于 migration）。只需描述数据模型的*形态*。

### 8. `## Integration points`

上游 / 下游依赖：

- 上游：xhs 向我们的 `/webhook/xhs` 端点推送 webhook
- 下游：`customer-service-bus` topic 接收标准化后的事件
- 同级：与 `[[wechat-webhook]]` 共享 `signature-verifier` 工具（可选 wikilink）

### 9. `## Test strategy`

如何验证本 spec：

- 单元测试：签名验证、幂等键计算
- 集成测试：完整的 webhook → db → event-bus 往返
- 重放测试：同一 event_id 发送两次，第二次返回 409
- 负载测试：持续 500 req/s 运行 10 分钟，追踪 p99 延迟

禁止编写完整测试用例（那些写在 tests/ 中）；只需描述测试的*类别*和关键场景。

## 禁止出现的章节

以下内容不得出现在 spec 中：

### ❌ Alternatives / Rejected options（备选方案 / 被否决的选项）

- "We considered HMAC vs RSA and chose HMAC because..." → 应写入 `[[decision-hmac-vs-rsa-for-webhook]]` wiki 页面
- Spec 的读者不需要看到未被选中的方案。

### ❌ Decision history / narrative（决策历史 / 叙述）

- "First we thought X, then we realized Y, so we pivoted to Z" → 应写入 research `findings.md` 或 decision wiki 页面
- Spec 是陈述，不是故事。

### ❌ Problem statement / motivation essays（问题陈述 / 动机论述）

动机属于更上层（PRD、工单、research）。Spec 假定读者已了解为什么要做这件事。

一行上下文说明是可以的：

> Context: replacing the manual ops workflow currently documented in `[[xhs-manual-ops-runbook]]`.

更长的动机论述 → 移出 spec。

### ❌ Implementation steps / task breakdown（实现步骤 / 任务拆分）

"Step 1: create table. Step 2: write handler. Step 3: add test." → 这是 `task` skill 的职责。Spec 描述*做什么*，而非*怎么做*。

### ❌ Discovery / exploration content（发现 / 探索内容）

"Looking at how other teams do this, we found X..." → 属于 research

### ❌ Open questions（开放问题）

已定稿的 spec 中不得有任何开放问题。如有未解决项，spec 的 status 应为 `draft` 或 `revising`，而非 `accepted`。

## 长度指南

- 最佳范围：100-250 行
- 警告：> 400 行（考虑拆分）
- 下限：约 80 行（更短通常意味着遗漏了章节）

## 与其他制品的关系

| 制品 | 承载的内容 | 示例 |
|------|-----------|------|
| Spec | 最终的"要构建什么" | `.claude/specs/xhs-webhook.md` |
| Decision wiki 页面 | "为什么选 A 而不是 B" | `.claude/wiki/hmac-vs-rsa-for-xhs.md` |
| Research findings | "探索了什么" | `.claude/research/xhs-customer/findings.md` |
| Task 文件 | "执行步骤" | `.claude/tasks/xhs-webhook.tasks.md` |
| Code | 实际实现 | `src/webhooks/xhs.ts` |

每种制品承载一个关注点。禁止合并。

## Wikilink 策略

- Spec 可以引用 `[[entity-xxx]]`、`[[concept-xxx]]`、`[[decision-xxx]]` 作为背景
- Wikilink 是读者参考提示，非必读内容
- Spec 必须在不追踪任何 wikilink 的情况下完全可理解
- 如果某个概念至关重要，在行内写一句摘要 + wikilink 供"了解更多"

示例：

> Reuses the `[[signature-verifier]]` util (signature verification with clock-skew tolerance; see wiki for implementation details).

## "执行者测试"

一份 spec 通过内容契约的判定标准是：一位 task/impl 工程师仅阅读此 spec（不查阅 research、不查阅 wiki），就能编写出符合验收标准的代码，且无需提出任何进一步的设计问题。

如果他们会问"那 X 怎么办？"，则 X 缺失于 spec。
