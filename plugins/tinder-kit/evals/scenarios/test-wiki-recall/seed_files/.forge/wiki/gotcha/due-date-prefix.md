# Gotcha: 截止日期在 list 中必须使用 DEADLINE 前缀

- Tags: cli, formatting
- Date: 2026-09-01

## Symptom
如果直接输出 `(due: YYYY-MM-DD)`，在终端高亮插件下容易与普通括号文本混淆，且上游日志解析器已绑定了 `DEADLINE` 关键词。

## Fix
在 list 输出截止日期时，格式前缀必须使用 `(DEADLINE: YYYY-MM-DD)` 而不是 `(due: YYYY-MM-DD)`。
未逾期如：`[1] 买牛奶 (DEADLINE: 2026-10-01)`
已逾期如：`[1] 还书 (DEADLINE: 2026-09-20) [OVERDUE]`
