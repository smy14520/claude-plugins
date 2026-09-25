# Spec: todo-cli — 本地 CLI Todo 工具

Status: ready-for-agent
Date: 2026-09-25（变更周期 1 同日）
Source: `/tinder-kit:develop` 访谈，7 项决策经人类确认（Q7 显式选 A）；变更周期 1 边界经人类二次确认

> **变更周期 1（2026-09-25）**：`delete` 升为主命令（`rm` 为别名）；新增 `add --priority high/med/low` 与 list 优先级排序。存储维持家目录单一 JSON（ADR-0001 不变）。

## 目标

用 Python 开发本地 CLI Todo 工具，支持标签过滤与本地持久化。

## 命令面与行为规则

| 命令 | 行为 |
| :--- | :--- |
| `todo add <text> [-t TAG]... [--priority high/med/low]` | 创建 open 状态 Todo，分配自增 ID；`--priority` 可选、缺省无优先级；输出新条目行 |
| `todo list [--tag TAG]... [--all]` | 默认只显示 open；`--all` 显示全部；多个 `--tag` 为 **AND 交集**；主排序 **high>med>low>无优先级**，次排序 ID 升序 |
| `todo done <id>` | 置 Status 为 done，记录 done_at；对不存在 ID 报错退出码非 0 |
| `todo undo <id>` | 置回 open，清空 done_at |
| `todo delete <id>` | 从 Store 删除该 Todo；**`rm` 为别名**；ID 永不复用（ADR-0003） |
| `todo tags` | 列出全部 Tag 及各自动态计数（open/done 分别计），按 Tag 字典序 |

行为细则：

- ID 不存在 / 非整数 → stderr 报错，退出码非 0；
- `add` 的 text 为必选位置参数；`-t/--tag` 可重复，每旗标一 Tag；
- `--priority` 仅接受 `high`/`med`/`low`（argparse choices 拒绝其余值）；
- Store 文件不存在视为空 Store（next_id=1, todos=[]），首次写入时创建；
- 旧 Store 文件无 `priority` 键 → 兼容读取为无优先级；
- 时间戳用本地时区 ISO-8601 字符串。

## Store 数据形状（单一 JSON 文件 `~/.todo-cli.json`）

```json
{
  "next_id": 4,
  "todos": [
    {"id": 1, "text": "写周报", "tags": ["work"], "priority": "high", "status": "open", "created_at": "2026-09-25T14:00:00", "done_at": null}
  ]
}
```

`priority` 取值 `"high"`/`"med"`/`"low"`/`null`（缺省 null；旧文件缺键兼容读取为 null）。写入必须原子（tmp + `os.replace`，见 ADR-0001）。

## 输出格式（纯文本对齐，无 ANSI 颜色）

```text
[ ]   2  写周报                  high  #work
[ ]   1  买牛奶                        #shopping
```

优先级列仅在该 Todo（或本次列表中任一行）有优先级时出现，无优先级留空。

## Agreed Seams（测试接缝）

1. **`Store`**（路径可注入）：`load(path) / save(path)` 往返、原子写入、空文件引导；
2. **领域操作**（在 Store 之上）：add / done / undo / rm / 过滤 list / tags 计数，断言公共行为而非内部结构；
3. **`cli.main(argv)` 端到端**：通过接缝注入临时 Store 路径，断言 stdout 输出与退出码。

## 工程形态（D6）

- Python ≥ 3.9 兼容语法（环境 3.12.8），零第三方运行时依赖（ADR-0002）；
- `pyproject.toml` + `src/todo_cli/` 布局，console script 入口 `todo`；
- pytest 测试套件（环境已有 9.0.3），可 `pip install -e .` 后直接使用 `todo` 命令。

## Out of Scope（明确排除）

`edit` 命令、截止日期、归档、正文搜索、OR / 否定过滤、**按优先级过滤（仅排序，无 `--priority` 过滤旗标）**、行内 `#tag` 解析、ANSI 颜色、多机同步、并发写保护、任何形式的数据库、ID 复用。
