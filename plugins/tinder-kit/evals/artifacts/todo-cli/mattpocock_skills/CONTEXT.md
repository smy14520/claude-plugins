# Todos

一个单机单用户的本地命令行待办工具。追求纯键盘极简交互：没有迁移、打包、鉴权、同步等负担。

## Language

**Task（任务）**:
用户要完成的一件事，是本工具唯一的一等记录。
_Avoid_: Item, todo, entry

**Open（未完成）**:
Task 的默认状态，尚未完成。新创建的 Task 总是 Open。
_Avoid_: Active, pending, todo（作为状态词）

**Done（已完成）**:
已完成的状态。Done 的 Task 保留在存储中，但默认不在列表中显示。
_Avoid_: Finished, closed, completed（作为状态词）

**Tag（标签）**:
任务上的自由字符串标注，一条 Task 可带多个。标签没有独立注册表——「存在哪些标签」永远是扫描 Task 得出的派生事实。标签匹配不区分大小写，显示保留输入原样，因此 `Work` 与 `work` 是同一个 Tag。
_Avoid_: Label, category, registry, tag rename（作为操作，不存在）

**Priority（优先级）**:
Task 的可选枚举属性，取值仅限 `high | med | low`，默认 `med`。闭集枚举：非法值在输入时报错，而非像 Tag 那样自由分裂。Priority 不参与排序——列表永远按创建顺序（ID 升序）稳定展开。
_Avoid_: Importance, level, urgent（那是 Tag 的事）

**ID（标识符）**:
Task 创建时分配的短整数，一经分配永不复用，永久指向同一 Task。ID 来自 list 输出，原样回填到后续命令中。
_Avoid_: UUID, 序号（list 显示位置不是 ID）

**Delete（删除）**:
物理删除：记录从存储中彻底消失，不可恢复。CLI 动词为 `delete`（`rm` 为别名）。
_Avoid_: Trash, archive, soft delete（这些概念不存在于本工具）
