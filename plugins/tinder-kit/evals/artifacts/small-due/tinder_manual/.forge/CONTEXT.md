# CONTEXT — 统一语言词汇表

本文件是项目的统一语言（Ubiquitous Language）真实源。
所有工单标题、Spec、代码命名、测试用例名必须使用此处定义的标准术语；
凡标注 _Avoid_ 的同义词一律禁止出现在上述产出中。

按需懒创建：术语在讨论中敲定一条，就登记一条。

---

## 术语表

### Due（截止日期）

任务被期望完成的日期。可省略；提供时以 `YYYY-MM-DD` 形式给出。
_Avoid_: deadline、到期时间、expiration

### Overdue（已逾期）

未完成任务的当前日期**严格晚于**其 Due。边界裁决：当前日期等于 Due 当天**不算** Overdue（截止当天仍是合法交付日）。
无 Due 的任务永远不会 Overdue。
_Avoid_: expired、超期、过期、late
