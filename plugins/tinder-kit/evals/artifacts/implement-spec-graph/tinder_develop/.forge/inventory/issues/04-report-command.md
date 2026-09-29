# 04 — report 补货报告命令

**What to build:** `stock report --threshold N`（默认 5）列出数量严格小于 N 的商品，格式与 `list` 一致（复用 list 的格式化，而不是另写一份）；没有需要补货的商品时打印 `nothing to restock`。

**Blocked by:** 01, 03

**Status:** resolved

- [x] 只列出低于阈值的商品，按名排序
- [x] 与 list 共用同一个格式化函数
- [x] 无低库存时打印 `nothing to restock`

## Comments

- 已合入 `integr/inventory`（tip `2c6d6c3`），pytest 23 passed。格式化复用共享 `format_items`，严格小于阈值，5 个行为测试在 `tests/test_cli_report.py`。至此 spec 的四张 ticket 全部落地。
- Review 后裁决追加：`--threshold` 改经共享 `parse_positive_int` 手写解析，非法输入 stderr 报错且退出码 1（对齐 spec 全局错误规则；qty 校验同步收紧为严格十进制）。见 commit `e2ad630` 之后的 fix commit。
