# Spec: Due Date 支持

Status: ready-for-agent

在极简 Todo CLI 上增加截止日期（Due）支持：`add --due` 与 `list` 的 Overdue 标注。

## 定案的 Decisions（grill 会话 2026-09-25）

| # | Decision | 内容 |
|---|---|---|
| D1 | 术语与数据形态 | 字段名 `due`，ISO `YYYY-MM-DD` 字符串；缺省时键整个省略；旧记录写回不补 `"due": null` |
| D2 | Overdue 语义 | 严格：当前日期晚于 Due 才标注；Due 当天不算。当前日期取本地时区 |
| D3 | list 展示 | `[id] title (due: YYYY-MM-DD)`，Overdue 行末尾追加 ` [OVERDUE]` |
| D4 | add 回显 | `Added #id: title (due: YYYY-MM-DD)`，与 list 同构 |
| D5 | 非法输入 | 非法日期格式友好报错 + exit != 0，零写入（校验在 argparse `type=` 纯函数 `parse_due`） |
| D6 | 过去日期 | 放行 — 补录早已逾期的事是真实场景，Overdue 机制覆盖 |
| D7 | 校验位置 | `parse_due` 纯函数 Seam 挂 argparse `type=`；逾期判定 `is_overdue` 可注入 today |
| D8 | 范围 | 排序、`--overdue` 过滤、edit/clear due 全部 out of scope；其余既有行为一律不动 |

## Out of Scope

- 按 due 排序 / `--overdue` 过滤参数
- 修改或清除已有任务的 due
- `load_todos` 对损坏文件的静默清空行为（既有 gotcha，另行开票）

## 验收标准

1. `todo add "x" --due 2026-10-01` → 记录含 `"due": "2026-10-01"`，回显 `Added #n: x (due: 2026-10-01)`
2. `todo list` → 未过期 due 任务显示 `(due: …)`；已过期行尾追加 `[OVERDUE]`；Due 当天不标
3. `--due tomorrow` 等非法输入 → 友好报错、exit code != 0、`.todos.json` 零写入
4. 旧版 `.todos.json`（记录无 due 键）读入正常；写回后旧记录不新增键
5. 测试覆盖：日期解析、逾期判定（含边界）、旧文件兼容
