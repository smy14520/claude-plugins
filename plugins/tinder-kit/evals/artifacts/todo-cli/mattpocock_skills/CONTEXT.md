# Todo CLI

一个本地单人使用的命令行待办工具：以一次性子命令操作一个全局清单，标签是唯一的组织维度，优先级决定排列的先后。

## Language

**Todo**:
一条待办事项，工具的最小单位；由标题、标签、优先级、完成状态构成，创建即处于未完成状态。
_Avoid_: Task, Item, 事项, 条目

**标签（Tag）**:
挂在 Todo 上的自由文本标记，一条 Todo 可挂零个或多个，同一标签可被任意多条 Todo 共享；按多条标签过滤时指"每条都具备"（AND）。
_Avoid_: Category, Label, 分类

**优先级（Priority）**:
Todo 的紧急程度，只有 high / med / low 三档，缺省为 med。
_Avoid_: 紧急度, importance, severity

**已完成（Done）**:
Todo 的终态；从未完成到已完成是一次单向转换，转换发生的时刻会被记下。
_Avoid_: finished, closed, 勾选

**清单（the list）**:
全部 Todo 共存于唯一的全局清单，不按项目或目录划分；组织职责由标签承担，而非清单划分。
_Avoid_: workspace, 项目, 集合
