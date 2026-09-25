# 03 路由匹配器

Status: resolved
Type: task

## What

`src/mock_server/matching.py`：`strip_query(target)` 与 `match_route(routes, method, target) -> Matched | MethodNotAllowed | NotFound` 纯函数。语义按 spec §2：忽略 query、尾斜杠严格区分、method 大小写不敏感、first-wins、405 时携带 `allowed` 方法元组。

## 验收标准

- [ ] 不接触任何 I/O，可作为纯函数穷举测试
- [ ] `tests/test_matching.py` 覆盖：精确命中 / query 忽略 / 尾斜杠 / 405+allowed / 大小写 / first-wins / 空 routes

## Comments

- 已完成：`tests/test_matching.py` 9 项全绿。实现期补钉语义：HEAD 不回退 GET 路由（严格 405），已同步 spec §2 与 README。
