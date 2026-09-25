# CONTEXT — 统一语言词汇表

> 本文件是 todo CLI 项目的领域术语唯一真实源。所有工单标题、测试用例名、变量名、输出列名必须使用下列标准术语，严禁漂移到 _Avoid_ 列的同义词。
> 本文件只是词汇表——实现细节（存储格式、路径、库选型）一律属于 spec 与 ADR 的领地。

## 术语表

| 术语 | 定义 | _Avoid_ |
| :--- | :--- | :--- |
| **Task** | 一条待办事项：一个标题、零个或多个 Tag、一个 Priority、一个 Status。工具管理的核心实体。 | item, entry, record, "一条 todo" |
| **Todo** | 指 CLI 工具本身（todo CLI）。绝不用于指代单条 Task。 | 用 "todo" 指代条目 |
| **Status** | Task 的完成状态，仅两态：`pending`（未完成）/ `done`（已完成）。不存在第三状态；"放弃"用 delete 表达。 | open/closed, active, cancelled（作为状态） |
| **Tag** | 挂在 Task 上的自由形式分类标记；一个 Task 可挂零个或多个，用于 list 过滤。 | label, category, group |
| **Priority** | Task 的紧急度档位，固定三档：`high` / `med` / `low`。 | severity, importance, urgency |
| **ID** | Task 创建时分配的自增整数，命令以此引用 Task。 | 行号, index, uuid |
