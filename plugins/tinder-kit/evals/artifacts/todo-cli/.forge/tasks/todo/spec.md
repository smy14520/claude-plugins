# Python 本地 CLI Todo 工具：标签过滤与本地持久化

## Goal

用 Python（纯 stdlib）开发本地 CLI Todo 工具 `todo.py`：支持 `+tag` 内联标签、多标签交集过滤、
`--priority high|med|low` 三档优先级，数据持久化为当前目录单一 JSON 文件 `.todos.json`。
pytest 先红后绿，核心行为全部有测试背书。

## Latent Assumptions Exposed

（已经用户 Round 1 确认或未提异议生效）
- A1: 单用户本地工具，无并发写、无文件锁需求（用户未异议）
- A2: 数据规模百级以内，性能非考量（用户未异议）
- A3: 无云同步 / 多设备共享（用户未异议）
- A4: 以 `python3 todo.py ...` 直接调用，不做 pip 打包发布（用户未异议）
- A5: 文本支持中文，文件 UTF-8 编码（用户未异议）
- A6: 依赖策略取推荐项 —— 纯 stdlib（argparse + json），零第三方依赖（用户未提异议，按推荐生效）
- A7: （**v1.2 终拍**）缺省存储 = 用户主目录 `~/.todos.json` 单一 JSON 文件；`TODO_FILE` 环境变量覆盖路径（兼作测试接缝）。用户多轮拍板中以最新「写死」口径为准（v1.0 曾暂定 cwd，v1.2 迁主目录）
- A8: `--priority` 缺省值为 `med`
- A9: todo id 为持久化稳定整数（新增时取 max(id)+1，起始 1），`done`/`delete` 按此 id 寻址（v1.1 随命令更名同步）

## Agreed Seams

- **Seam 1: 存储层往返契约** — `storage.load(path) / storage.save(path, todos)`
  - 预期行为: save→load 往返无损（id/text/tags/priority/done/created_at 全字段）；文件为 UTF-8 JSON 数组；
    文件不存在时 load 返回空列表；save 采用「临时文件 + 原子 rename」防半写损坏；**绝不使用任何数据库**
  - 验证命令/用例: `pytest tests/test_storage.py`（往返、缺省空表、原子写、中文 UTF-8）

- **Seam 2: 领域逻辑契约** — 标签解析 / 优先级 / 过滤
  - 预期行为: `add "买牛奶 +shopping +urgent" --priority high` → text=`买牛奶`、tags=`{shopping, urgent}`、priority=`high`、done=False；
    未识别的 `+token` 一律收为标签；`--priority` 仅接受 `high|med|low`，非法值报错退出码 ≠ 0；
    `list --tag a --tag b` 为**交集**过滤；`--all` 含已完成，默认隐藏已完成；排序 = 优先级(high>med>low) → id 升序
  - 验证命令/用例: `pytest tests/test_domain.py`（解析、三档校验、交集、排序、隐藏/显示已完成）

- **Seam 3: CLI 端到端契约** — `python3 todo.py <subcommand>`（**v1.1 修订**：命令面收敛为四个）
  - 预期行为: `add`/`list`/`done`/`delete` **四命令**（v1.0 的 `rm` 更名 `delete`；`tags` 命令按用户拍板裁撤）；`done <id>`/`delete <id>` 幂等寻址，id 不存在时非零退出码 + 错误信息到 stderr；
    `list` 输出 `[id] [优先级] [状态] 文本 #标签`，已完成项以 `[x]` 标记，`--tag` 交集过滤，`--all` 显示已完成；
    存储路径 = `$TODO_FILE` 或缺省 `~/.todos.json`（**v1.2**：由 cwd 迁用户主目录，用户终拍写死）
  - 验证命令/用例: `pytest tests/test_cli.py`（进程内调用 `main(argv)` + `TODO_FILE` 指向 tmp_path + capsys 断言输出与退出码）

## Empirical Findings

<!-- 原型探针（prototype）实证结论，无则写“无” -->
- 无（
