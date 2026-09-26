# todo-cli MVP 终报（2026-09-26）

## 交付物

`todo` CLI：`src/todo_cli/{cli,core,store}.py`（cli→core→store 无环），uv 包 `todo-cli`，console_script `todo = "todo_cli.cli:main"`，Python >= 3.12，运行时依赖 `[]`（纯标准库），dev 仅 pytest + ruff。命令面 7 条：add / list / done / reopen / rm / edit / clear。

## 验收与证据

- PRD：`.arbor/tasks/todo-cli/prd.md`，32 条验收全部兑现，独立 PRD 审查两轮至 clean（首轮 2 条 serious gap 已修复关闭）。
- gate：S-001..S-005 全部经 `seed done` 翻绿，日志在 `done-logs/`（测试数递进 6→14→19→25→46）。
- 客观锚（主会话重放）：`uv run pytest` → 47 passed / 1.93s；`uv run ruff check .` → All checks passed；冷环境 `rm -rf .venv && uv sync && uv run pytest` 全绿。
- 真实产物演示（干净临时目录）：AND 标签收窄、优先级排序、done/`--all` 生命周期、ID 不回收（next_id 持久计数）、`--json` 可 json.load、错误路径 exit 1 + stderr、目录仅 `.todos.json` 无任何数据库产物。
- 流分离实测：视图命令 stdout 纯净（list --json 可被 json.load）；变更类命令确认行在 stdout（含新 id，AC 钉死）；错误与提示一律 stderr。

## 关键实现决策（续接必读）

1. `allocate_id = max(next_id, max(id)+1)`：仅在手改文件计数器落后时向上抬，永不回退/复用。
2. 读时 schema 双向校验（done=true ⇒ completed_at 必为 string），防脏文件让排序 TypeError；StoreError → exit 1，不 traceback。
3. `--tag ""` / `--tag ","` 全空段判 argparse 用法错误（静默等于无过滤太危险）；尾随空段忽略（AC 钉死）。
4. 时间戳 UTC 秒级 `%Y-%m-%dT%H:%M:%SZ`，字典序==时间序；已完成段同秒 tie-break 按 id 降序。
5. 原子写：同目录 `.todos.json.tmp` + flush/fsync + `os.replace`，替换失败删 tmp 原样重抛。
6. 标题原样存储不 trim（strip 后为空才拒绝）；BrokenPipeError → exit 0。

## 与 PRD 偏差

无。32 条验收逐条兑现。

## Backlog（MVP 后再议，用户已拍板不影响本期验收）

- `edit` 增加"清空 tags"的参数（当前 edit 只能整体替换、无法清空）。
- `--any`（OR 标签过滤）——PRD Out of Scope 预留的纯增量。
- 导出（如 markdown/csv）。
- 深审 review-loop（代码审计+产物审计+对抗证伪）。

## 遗留说明

- S-002 门后补的 tie-break 测试不在 S-002 gate 日志内（gate 已完成后补测；全量 47 条已单独验证绿）。
- PRD 措辞修正一次：Design"stdout 纯净"收窄为按命令分类（与 AC"add 的 stdout 含新 id"对齐），见 prd.md 跨片联动节。
