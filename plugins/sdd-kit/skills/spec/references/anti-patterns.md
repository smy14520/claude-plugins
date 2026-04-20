# Spec 反模式

已观察到的失败模式。全部应避免。

---

## 1. 理由堆砌

**症状**：spec 中包含每个设计选择的多段落论证。

**错误原因**：spec 是契约，不是论文。执行者不需要重新推导逻辑；他们需要知道要构建什么。

**修正**：将理由移至 `[[decision-xxx]]` wiki 页面。Spec 只记录结论。

---

## 2. 保留备选方案

**症状**：spec 中有"Alternatives considered"章节，列出被否决的选项。

**错误原因**：被否决的选项在执行阶段是噪音。还会在 impl 阶段诱发犹豫和反复。

**修正**：方案对比写入 decision wiki 页面（或 research findings）。Spec 只保留最终选定的方案。

---

## 3. 叙述式 spec

**症状**：spec 读起来像故事——"First we tried X. Then we hit Y. So we changed to Z."

**错误原因**：历史不是契约。叙述式写法使阅读时间翻倍，且不增加任何可操作信息。

**修正**：改写为平铺陈述。"Uses Z because of Y constraint."（如果连这个因果从句也趋向叙述，就删掉，让 `[[decision-xxx]]` 页面承载原因。）

---

## 4. 模糊约束

**症状**："should be fast"、"should be secure"、"should be reliable"。

**错误原因**：无法操作。task/impl 无法判断约束何时满足。

**修正**：使用数值或二元判定。`p99 < 200ms`、`signature verified per RFC xxx`、`at-least-once delivery`。

---

## 5. 多功能 spec

**症状**：一个 spec 覆盖"xhs webhook + 管理后台 + 从 wechat 迁移"。

**错误原因**：验收标准变得模糊；任务拆分跨功能纠缠；review 变成全有或全无。

**修正**：一个功能一个 spec。相关 spec 可以通过 `supersedes` / `related-specs` frontmatter 相互引用。

---

## 6. spec 中包含实现步骤

**症状**：spec 包含"Step 1: create migration. Step 2: write handler. Step 3: add test."

**错误原因**：这是 task skill 的职责。Spec 回答"做什么"而非"怎么做"。

**修正**：描述终态（数据模型、接口、不变量）。让 `task` 负责拆解。

---

## 7. 将 research 泄漏到 spec 中

**症状**："Looking at how wechat does it..." / "After exploring 3 options..."

**错误原因**：spec 中的 research 内容模糊了关注点分离。未来读者必须分辨"这是发现还是承诺？"

**修正**：research findings 保留在 `.claude/research/<topic>/findings.md`。Spec 只提取最终的承诺。

---

## 8. 空白的 non-goals

**症状**：non-goals 章节缺失或写"none"。

**错误原因**：范围必然蔓延。每个非平凡功能都有可能溢出的邻近领域。

**修正**：强制至少 2 条明确的 non-goals。示例："does NOT replace existing wechat handler"、"does NOT handle outbound messages"、"does NOT introduce a new queue system"。

---

## 9. 带着未解决的 `<TODO-DECIDE>` 就定稿

**症状**：spec status = `accepted` 但 grep 仍能找到 `TODO-DECIDE` 或 `TBD`。

**错误原因**：下游 impl 会撞上未定义之处并被迫重新决策，违反"执行者不做决策"原则。

**修正**：Finalize 步骤必须在发现任何未解决标记时阻止定稿。禁止自动 accept。

---

## 10. 自动推进到 task

**症状**：在 Finalize 阶段，spec skill 自动调用 task skill 并开始拆解。

**错误原因**：违反"阶段独立"原则。用户可能希望：

- 暂停等待 review
- 跳过 task（对于小 spec，直接进入 impl）
- 将 spec 交给其他人 / 其他 agent

**修正**：Finalize 以摘要 + 下一步*建议*结束。用户在准备好时显式运行 task skill。

---

## 11. 复制 wiki 内容

**症状**：spec 将 `[[entity-xxx]]` 或 `[[concept-xxx]]` 的完整内容复制到自身中。

**错误原因**：wiki 失去权威性；spec 膨胀；变更后产生不一致。

**修正**：链接到 wiki 页面，在行内写一句摘要作为上下文：

> Reuses `[[signature-verifier]]` (HMAC-SHA256 with configurable clock-skew tolerance).

---

## 12. 验收范围不足

**症状**：验收标准只覆盖正常路径。

**错误原因**：impl 会在缺少错误处理、重放、边界情况的情况下交付；task 也不会覆盖这些。

**修正**：验收标准必须覆盖：

- 正常路径
- 至少一条校验失败路径
- 幂等性 / 重放（如相关）
- 可观测性（必须发出的 metric/log/trace）

---

## 13. 过度指定实现细节

**症状**：spec 写"使用 Redis 配合 LUA 脚本，表必须使用 PostgreSQL 配 BRIN index"。

**错误原因**：除非该选择是硬性约束（如团队标准），否则会过度绑定 impl。Impl 可能发现更好的方案。

**修正**：指定*能力*（"幂等存储，24h TTL"），而非技术选型，除非该技术本身就是硬约束。

---

## 14. 缺少测试策略的 spec

**症状**：`## Test strategy` 章节缺失或只写"will be tested"。

**错误原因**：impl 会低估测试；验收标准将无法验证。

**修正**：列出测试类别（unit / integration / load / manual），并指出每个类别必须覆盖的关键场景。
