# 定稿前流程与条件

PRD 定稿前需要完成两件事:扩展扫视和 PRD 收尾整理,然后才能调用 `sdd-arbor finalize-brainstorm`。

## 扩展扫视

扩展扫视是 brainstorm 内部的 diverge → converge 转折,**不是** research,也**不是**新阶段。

在初步 package scope 轮廓形成后、PRD 定稿前,简短扫一遍:

- **未来演进**:哪些能力很快会被需要,但不一定进本次 PRD scope?
- **相关场景**:有没有相邻用户流 / 系统流会影响当前边界?
- **失败与边界**:哪些异常、权限、数据、迁移或回滚边界容易漏?

让用户选择:哪些纳入本次 PRD scope,哪些明确写入 `Out of scope`。扫视结果必须写回 `Requirements (evolving)` / `Out of scope` / `Acceptance Criteria (evolving)`,再进入 finalize。

## Open Questions 处理

进入收尾前先处理 PRD 里的 `Open Questions`:

- **Blocking**:会改变本次交付 scope、数据模型、权限、接口、测试或验收的,下一轮必须优先追问。
- **Non-blocking**:不影响本次实现的,移入 Out of scope / Risks / Assumptions,并写清处理方式;不要继续留在顶层 `Open Questions` 阻塞 finalize。

## PRD 收尾整理

把 evolving 内容落入正式 section,填实背景、目标、In scope、Out of scope、关键场景、交付物、Package artifacts、Technical Framing、Slices、验证重点和风险;删除模板示例、占位符和空 section;顶层 `Open Questions` 必须为空或只保留明确标注为 non-blocking 的项。

删除 `## What I already know` 段——此时它的内容已经沉淀到 Requirements、Technical Framing、Slices 里,留着只增加 impl 阶段的噪音。（finalize 工具会自动剥离该段,但 brainstorm 应在提交 PRD 前主动整理,避免依赖工具兜底。）

## 自检

收尾整理完成后,先自检 PRD,自检不通过时继续编辑 PRD,**不要询问用户确认定稿**:

- 不得残留 `<...>`、示例 `SRC-LOCAL-001`、示例 slice、空的正式 section。
- Slices 必须是针对当前 PRD 的可执行切片。

## 定稿条件

只有同时满足以下条件,才可以整理 PRD 并调用 `sdd-arbor finalize-brainstorm`:

- Blocking questions 已解决,剩余 open questions 不阻塞 impl / review。
- Technical Framing 已覆盖承重技术边界;未知承重项不能留给 impl 猜。
- 扩展扫视已完成,结果已写入 Requirements / Out of scope / Acceptance Criteria。
- Acceptance Criteria 覆盖核心路径和关键失败 / 边界路径。
- Slices 已写好，按依赖顺序列出当前 PRD 的实现切片；不能保留示例 slice 或 `<...>`。
- 每个 slice 有对应的 `slices/S-NNN.md` task 文件，且包含非空的 `## Acceptance` 和 `## Verification` 段。
- PRD 已从 evolving 区整理进正式结构,保留必要决策和来源,避免访谈流水污染最终交付物。
- PRD 不再残留 `<...>` 模板占位符、示例 source、空 section;`背景与问题`、`目标`、`本次范围`、`关键场景`、`交付物清单`、`Package artifacts`、`Technical Framing`、`Slices`、`验证重点` 都必须是可执行内容。
- 顶层 `Open Questions` 中没有 blocking question;若保留 non-blocking 问题,必须说明为什么不阻塞本次 impl / review。
- 用户确认最终摘要。

## Finalize 命令

参数以 `sdd-arbor finalize-brainstorm --help` 为准。
