# Spec: todo-cli

Status: ready-for-agent

> 本 spec 是 `/grill-with-docs` 两轮访谈（Round 1–2）的沉淀结论。领域术语以 `.forge/CONTEXT.md` 为准；存储决策见 ADR-0001。

## 目标与边界

单机个人 Todo CLI。**坚决不做**（Out of Scope）：Web/GUI、多用户与鉴权、网络同步、任何数据库、并发控制。

全部功能边界 = **四个命令 + Tag 过滤 + 三档 Priority**，不再扩。

## 命令面（锁定）

| 命令 | 签名 | 行为 |
| :--- | :--- | :--- |
| `add` | `todo add <title> [--tag <tag>…] [--priority high\|med\|low]` | 创建 Task，输出新 ID |
| `list` | `todo list [--tag <tag>…] [--all]` | 默认仅 pending；`--all` 全量；多 `--tag` 为 **AND**；排序 Priority(high→med→low) 再 ID 升序 |
| `done` | `todo done <id>` | 置 Status=done（幂等）；ID 不存在 → 报错，退出码 1 |
| `delete` | `todo delete <id>` | 物理移除；ID 不存在 → 报错，退出码 1 |

## 领域语义

- **Priority**：三档 `high|med|low`；`add` 省略时默认 `med`；创建后不可变更（无 edit 命令）。
- **Tag**：自由形式；规范化为**小写、内部空白折叠为连字符**；同一 Task 去重保序；创建后不可增删。
- **ID**：自增整数，从 1 起，**删除后永不复用**（由存储中的 `next_id` 计数器保证）。
- **修正工作流**：打错标题 → `delete` + 重新 `add`。

## 输出格式（list）

四列对齐：`ID · Priority · Tags · Title`；`--all` 模式下 Status=done 的行前缀 `✓`，pending 行前缀空格；Tags 为空显示 `-`。

## 持久化（ADR-0001）

- 单一 JSON 文件，**跟随当前工作目录**（`cwd/.todos.json`，Round 2 Q9 拍板）——在哪个项目里跑，就是哪个项目的清单。
- 结构：`{ "version": 1, "next_id": <int>, "tasks": [ {id, title, tags[], priority, status} ] }`（刻意不含时间戳等未访谈字段）。
- 写入：直接整体覆写；文件不存在视为空库；损坏 JSON → 报错退出码 1。

## 技术栈

- Python `>= 3.10`（开发与运行于 Anaconda 3.12.8）。
- CLI 框架 **typer**；输出为纯文本对齐列（不依赖 rich）。
- 安装：`uv tool install --editable <repo>`，console script 入口 `todo`；备胎 `python3 -m todo_cli`。

## 验收清单

- [x] 四命令行为与上表一致（冒烟：add/list/done/delete 全通，错误路径退出码 1）
- [x] Tag 规范化（小写/空白→连字符/去重保序）生效（`Shopping`→`shopping`、`deep work`→`deep-work`）
- [x] 多 `--tag` AND 过滤 + Priority 排序正确（`test_select_filters_and_sorts`）
- [x] ID 永不复用（delete 2 后 add 分配 4，落盘 `next_id: 5`）
- [x] cwd 语义：不同目录互不干扰（`test_cwd_isolation`）
- [x] `uv tool install --editable` 安装后 `todo` 命令可用（typer 0.27.2，7/7 测试通过）
