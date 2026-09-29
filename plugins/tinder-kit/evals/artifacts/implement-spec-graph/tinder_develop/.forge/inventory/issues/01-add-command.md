# 01 — add 入库命令

**What to build:** `stock add <name> <qty>` 把数量累加到该商品（不存在则新建），并打印 `<name>: <新数量>`。`qty` 必须是正整数，否则报错退出码 1。

**Blocked by:** None — can start immediately

**Status:** resolved

- [x] 新商品入库后打印并持久化数量
- [x] 已有商品数量累加
- [x] qty 非正整数时 stderr 报错、退出码 1、库存不变

## Comments

- 已合入 `integr/inventory`（tip `049af37`），pytest 10 passed。6 个行为测试在 `tests/test_cli_add.py`（非法 qty 四种参数化，退出码 1 而非 argparse 的 2）。
