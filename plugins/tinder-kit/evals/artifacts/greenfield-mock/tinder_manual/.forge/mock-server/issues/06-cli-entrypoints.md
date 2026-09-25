# 06 CLI 与双入口

Status: resolved
Type: task

## What

`src/mock_server/cli.py`：`build_parser()` + `main(argv) -> int`，子命令 `serve`/`check`（spec §3/§4：旗标默认值、fail-fast 报错、check 全量报错与路由表、横幅、Ctrl+C 优雅退出、OSError 友好报错）；`__main__.py` 支持 `python -m mock_server`。

## 验收标准

- [ ] `mock-server serve --help` / `check --help` 完整
- [ ] `check` 三分支：通过 exit 0 打路由表 / 失败 exit 1 全量错误 / 文件缺失 exit 1
- [ ] `serve` 契约非法 fail-fast exit 1；`python -m mock_server` 与 console script 行为一致
- [ ] `tests/test_cli.py` 直测 `main(argv)`（serve 分支由冒烟验证覆盖）

## Comments

- 已完成：`tests/test_cli.py` 6 项全绿，含 `_thread.interrupt_main()` 真实 KeyboardInterrupt 优雅退出路径（外部 SIGINT 在评估沙箱不可投递，故以进程内证据替代）。`.venv/bin/mock-server --version` 与 `python -m mock_server --version` 输出一致。
