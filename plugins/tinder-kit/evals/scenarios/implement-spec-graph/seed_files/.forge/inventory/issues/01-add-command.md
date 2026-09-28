# 01 — add 入库命令

**What to build:** `stock add <name> <qty>` 把数量累加到该商品（不存在则新建），并打印 `<name>: <新数量>`。`qty` 必须是正整数，否则报错退出码 1。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 新商品入库后打印并持久化数量
- [ ] 已有商品数量累加
- [ ] qty 非正整数时 stderr 报错、退出码 1、库存不变
