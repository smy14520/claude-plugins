# 02 — remove 出库命令

**What to build:** `stock remove <name> <qty>` 从该商品扣减数量并打印 `<name>: <剩余数量>`；降为 0 时从库存删除并打印 `<name>: 0`。商品不存在或库存不足时报错退出码 1，库存不变。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 正常扣减并持久化
- [ ] 扣到 0 时删除该商品
- [ ] 不存在 / 不足时 stderr 报错、退出码 1、库存不变
