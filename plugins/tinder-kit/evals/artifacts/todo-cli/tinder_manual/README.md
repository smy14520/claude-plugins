# tdo — 本地 CLI Todo

单用户、零运行时依赖（纯 Python 标准库）的命令行待办工具：标签过滤 + 本地单 JSON 文件持久化。

## 安装

```bash
uv tool install .        # 在本仓库目录内执行
# 或: pip install .
```

要求 Python ≥ 3.10。

## 快速上手

```bash
tdo add "买牛奶" --tag shopping --tag urgent   # 录入（--tag 可重复，逗号=多标签）
tdo ls                                        # 列出未完成，按 ID 升序
tdo ls --tag shopping --tag "work,urgent"     # 多个 --tag 取交集；单个 --tag 内逗号取并集
tdo ls --all                                  # 连已完成一起列出
tdo ls --json                                 # 机器可读输出
tdo done 3                                    # 完成（幂等）
tdo reopen 3                                  # 退回未完成（幂等）
tdo rm 3                                      # 删除（硬删，无确认）
tdo tags                                      # 全部标签及计数，按计数降序
```

行格式：`[ ] 3 买牛奶 #shopping`，`[x]` 表示已完成。

## 存储

- 数据文件：`~/.todo/todo.json`；环境变量 `TODO_HOME` 可覆盖目录
- 每次写盘前旧文件轮转为 `todo.json.bak`（只保留上一代）
- 文件损坏时工具拒绝读取并提示从 `.bak` 恢复，绝不静默改写
- 架构决策详见 `.forge/wiki/decision/0001-single-json-file-storage.md`

## 开发

```bash
pip install -e '.[dev]'   # 或: uv pip install -e '.[dev]'
pytest
```

运行时零第三方依赖；`pytest` 仅为 dev 依赖。测试覆盖：存储 roundtrip、过滤逻辑、ID 分配。
