# CLAUDE.md — 项目标准（todo 本地 CLI）

本文件是本项目的现行工程标准。历史任务档案在 `.forge/tasks/`（spec 已冻结，仅作历史，不得当作现时标准加载）。

## 硬边界（红线，任何改动不得逾越）

- **存储**：仅 `~/.todos.json` 单一 JSON 文件（UTF-8 数组）；`$TODO_FILE` 环境变量可覆盖（测试接缝）。
- **零数据库**：禁止 SQLite / Postgres / 任何 DB 引入。
- **零网络 / 零 GUI**：禁止 Web、多用户、跨机同步相关代码。
- **零第三方依赖**：运行时与测试均纯 stdlib（当前：argparse + json + pytest）。
- **命令面封闭**：仅 `add` / `list` / `done` / `delete` 四命令；不加别名；扩命令需先修订契约。

## 功能契约（v1.2 终态）

- `add "文本 +tag1 +tag2" --priority high|med|low`：`+token` 剥离为标签，priority 缺省 `med`，仅此三档。
- `list --tag A --tag B`（多标签**交集**）`--all`（含已完成，默认隐藏）；排序 = priority(high>med>low) → id 升序。
- `done <id>` / `delete <id>`：稳定整数 id 寻址（新增取 max+1，起始 1）；幂等；id 不存在 → stderr + rc=1；argparse 错误 rc=2。

## 工程纪律

- **纯 stdlib + pytest TDD**：行为改动一律先写测试见红、再实现转绿；三条 Seams（storage 往返/原子写、domain 纯逻辑、CLI 端到端）必须保持全覆盖。
- **CLI 可测接缝**：`main(argv) -> int` 供进程内调用；测试经 `$TODO_FILE` 注入 `tmp_path`，用 capsys 断言输出与退出码。
- **测试隔离铁律**：conftest autouse 夹具强制 `TODO_FILE`；涉及缺省路径的用例必须 monkeypatch `$HOME`，**绝不触真实 `~/.todos.json`**，并断言 cwd 零污染。
- **架构单向依赖**：`todo.py`（薄 CLI 壳）→ `domain.py`（纯逻辑，零 IO）/ `storage.py`（tempfile + fsync + `os.replace` 原子写）；domain 不得 import storage/todo。
- 提交前 `python3 -m pytest -q` 必须 100% 通过。

## 已知低风险遗留（可作后续任务输入）

- 损坏 JSON 文件 fail-loud 但呈裸 traceback（未友好化）。
- `--help` / 空库输出 / 损坏文件路径尚无测试覆盖。
