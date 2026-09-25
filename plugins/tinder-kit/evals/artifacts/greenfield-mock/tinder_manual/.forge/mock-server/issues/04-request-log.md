# 04 请求日志

Status: resolved
Type: task

## What

`src/mock_server/request_log.py`：`format_log_line(now, method, target, status, elapsed_ms, note=None)` 纯函数（spec §5 格式，本地时间，耗时一位小数）+ `RequestLog`（sink 可注入，默认 `sys.stdout`）。

## 验收标准

- [ ] 无标记行：`[2026-09-25 18:05:01] GET /api/user -> 200 (3.0ms)`
- [ ] 有标记行：`... -> 404 (no mock) (0.4ms)`
- [ ] `tests/test_request_log.py` 用固定 `datetime` 断言精确格式，StringIO 捕获 sink

## Comments

- 已完成：`tests/test_request_log.py` 5 项全绿（固定时间戳精确断言 + StringIO sink）。
