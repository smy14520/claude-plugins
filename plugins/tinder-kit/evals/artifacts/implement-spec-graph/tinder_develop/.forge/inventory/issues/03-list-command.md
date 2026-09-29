# 03 — list 库存列表命令

**What to build:** `stock list` 按商品名排序，每行打印 `<name>: <qty>`；库存为空时打印 `(empty)`。

**Blocked by:** None — can start immediately

**Status:** resolved

- [x] 按商品名排序输出
- [x] 空库存打印 `(empty)`

## Comments

- 已合入 `integr/inventory`（fast-forward 至 `0af0cf0`，feat(cli): list 库存列表命令），pytest 4 passed。共享函数 `format_items` 由此 ticket 定义，供 04 复用。
