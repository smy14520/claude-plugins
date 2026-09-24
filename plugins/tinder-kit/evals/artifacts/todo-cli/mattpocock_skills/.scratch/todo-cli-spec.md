# Todo CLI — 已敲定的决策

来自 2026-09-24 的 /grill-with-docs 会话。术语见根目录 CONTEXT.md，存储决策见 docs/adr/0001。

## 用户拍板

- 一次性子命令，不做 TUI；子命令恰为 `add` / `list` / `done` / `delete`（带别名 `ls` / `rm`），不加 edit/undone。
- 持久化：单一本地 JSON 文件 `~/.todos.json`，坚决不用 SQLite 或任何数据库（ADR-0001）。
- Todo 字段：`id`、`title`、`tags`（字符串列表，一条可挂多个）、`priority`、`done`、`created_at`、`completed_at`。
- `--priority high|med|low` 是 add 的硬需求（不是 YAGNI），缺省 `med`。

## 实现采用的缺省（用户未逐一表态，可否决）

- `id`：单调递增整数，持久化于 `next_id`；删除后**不复用**编号。
- `list` 默认隐藏已完成；`-a/--all` 含已完成；`--done` 仅已完成。
- 多标签过滤为 AND（"每条都具备"）；`--tag` 可重复使用，也可逗号分隔；去重、保留大小写。
- 排序：优先级 high→med→low，其次创建时间升序。
- `done` 幂等：对已完成的 todo 重复 done 不报错，也不覆盖 `completed_at`。
- `delete` 立即硬删除，无确认、无回收站。
- 标题可不加引号（多个词以空格连接）；损坏的存储文件 → 报错退出（exit 1），绝不写回。
- 零第三方依赖（仅标准库 argparse），Python 3.10+；测试用 unittest。
- `TODO_STORE` 环境变量可覆盖存储路径（测试与高级用法留的缝）。
