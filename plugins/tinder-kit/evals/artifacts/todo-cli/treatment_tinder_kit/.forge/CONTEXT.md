# CONTEXT — 统一语言词汇表

本文件是 todo-cli 项目的领域词汇真实源。所有工单标题、代码标识符、测试用例名称与用户可见文案涉及以下概念时，必须使用 Canonical Term，严禁使用 _Avoid_ 列中的同义变体。

| Canonical Term | 定义 | _Avoid_ |
| :--- | :--- | :--- |
| **Todo** | 一条待办的原子事项，本工具管理的唯一核心实体 | task, item, entry, note, 事项 |
| **Tag（标签）** | 挂在 Todo 上的自由短词，仅用于归类与过滤；无层级、无预设集合、无数量上限 | label, category, 分类, topic |
| **Priority（优先级）** | Todo 的三档重要度 `high`/`med`/`low`，可缺省；仅用于 list 排序（high>med>low>无），不做优先级过滤 | importance, level, severity, 等级 |
| **Status（状态）** | Todo 的二态生命周期：`open`（未完成）或 `done`（已完成），无中间态、无第三态 | pending, in-progress, finished, completed, archived |
| **ID（编号）** | Todo 的唯一引用号，按创建顺序自增分配；一经分配永不改变、永不回收复用 | uuid, index, key, 序号（暗示位置） |
| **Store（清单存储）** | 全部 Todo 与 ID 分配计数所在的唯一持久化载体，全局仅此一份 | database, db, repository, 数据库 |
| **Filter（过滤）** | list 时按标签缩小显示范围的动作；多个 Tag 为交集关系 | search, query, 搜索 |
