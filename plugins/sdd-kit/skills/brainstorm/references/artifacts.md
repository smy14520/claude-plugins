# Package artifacts

当需求包含非平凡数据模型、第三方协议、OpenAPI、状态机、事件 payload 或权限矩阵时,在 `.arbor/tasks/<package>/artifacts/` 写 package-local design artifact,并在 PRD 的 `Package artifacts` / `数据 / 接口备注` / `Sources` 中引用。

## 原则

- Artifact 是 PRD 附属 contract,不是生产实现事实源。
- 新项目可用 `artifacts/data-model.sql` 压实草案级 schema contract;impl 后最终事实源是代码里的 migration / schema。
- 第三方集成可用 `artifacts/integration-contract.md` 记录 payload、验签、token、mock / real 边界。
- 不要把大段 SQL / 协议正文塞进 slice;slice 只引用 artifact 中的实体、协议或 contract。
- 若 impl / review 发现 artifact 错误或需要改变,走 amendment / NEEDS_CONTEXT,不静默偏离。
