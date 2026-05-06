# Amendment 入口

当 review 判定 BRAINSTORM_DRIFT 后回到 brainstorm 时,走 amendment 流程,不重开完整 grill-me 循环。

## 步骤

1. 读取 `task.json` 的 `review_result`,了解 drift 的具体原因。
2. 不重开完整 grill-me 循环。**只针对 drift 指出的问题追问确认**。
3. 用 PRD 的 `## Amendments / Forward-only corrections` 记录修正,**不静默改写已有需求**。每条 amendment 用 `AMD-001`、`AMD-002` 编号,写清 wrong / correct / affects / source。
4. 如果 amendment 影响 Slices(新增、删除或重排),同步更新 Slices 段。
5. 修正完成后重新 finalize。
