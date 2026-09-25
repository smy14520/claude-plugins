# Wiki Index — todo-cli 知识大盘

## Decision（ADR）

- [0001 单一 JSON 文件存储](decision/0001-single-json-file-storage.md) — 永不引入数据库的硬约束 + 原子写入，无并发锁
- [0002 零运行时依赖](decision/0002-zero-runtime-dependencies.md) — 只用 stdlib，放弃 click/typer
- [0003 ID 永不复用](decision/0003-id-never-reuse.md) — 持久自增计数器，防止旧 ID 引用静默错位

## Gotcha

（暂无——遇到坑时用 `/wiki` 沉淀）
