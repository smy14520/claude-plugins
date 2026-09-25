# todo

单机单用户的极简 CLI 待办工具：标签过滤 + 本地 JSON 持久化。纯标准库，零第三方运行时依赖（Python 3.10+）。

## 用法

```bash
./todo.py add "买牛奶" --tag 家 --priority high
./todo.py add "回邮件" --tag work

./todo.py                     # = todo list，只看未完成，按创建顺序
./todo.py list --tag work --tag urgent   # 多标签 AND，大小写不敏感
./todo.py list --priority high
./todo.py list --done         # 只看已完成
./todo.py list --all

./todo.py done 3              # 完成（可重复敲，幂等）
./todo.py reopen 3            # 手滑后悔药
./todo.py delete 3            # 物理删除；rm 为别名
```

优先级为闭集枚举 `high|med|low`（默认 `med`），非法值直接报错。列表永远按创建顺序（ID 升序）稳定展开；`!high` / `!low` 仅在非默认值时显示。

## 存储

所有数据在一个 JSON 文件里（默认 `~/.todos.json`，可用环境变量 `TODO_FILE` 覆盖），人类可直接阅读编辑。ID 来自持久化自增计数器，永不复用。写盘走临时文件 + 原子替换；文件损坏时拒绝读写、绝不覆盖。

## 设计文档

- [CONTEXT.md](./CONTEXT.md) — 领域语言（Task / Tag / Priority / ID / Done / Delete）
- [docs/adr/0001-single-json-file-storage.md](./docs/adr/0001-single-json-file-storage.md) — 为什么是单 JSON 文件而不是数据库

## 测试

```bash
python3 -m pytest
```
