# 04 — report 补货报告命令

**What to build:** `stock report --threshold N`（默认 5）列出数量严格小于 N 的商品，格式与 `list` 一致（复用 list 的格式化，而不是另写一份）；没有需要补货的商品时打印 `nothing to restock`。

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] 只列出低于阈值的商品，按名排序
- [ ] 与 list 共用同一个格式化函数
- [ ] 无低库存时打印 `nothing to restock`
