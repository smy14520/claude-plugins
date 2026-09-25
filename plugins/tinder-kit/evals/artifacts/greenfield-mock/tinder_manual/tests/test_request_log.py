"""请求日志格式的精确断言（固定时间戳 + StringIO sink）。"""

import io
from datetime import datetime

from mock_server.request_log import RequestLog, format_log_line

NOW = datetime(2026, 9, 25, 18, 5, 1)


def test_format_line_hit():
    line = format_log_line(NOW, "GET", "/api/user", 200, 3.04)
    assert line == "[2026-09-25 18:05:01] GET /api/user -> 200 (3.0ms)"


def test_format_line_keeps_query_in_target():
    line = format_log_line(NOW, "GET", "/api/user?page=1", 200, 0.4)
    assert line == "[2026-09-25 18:05:01] GET /api/user?page=1 -> 200 (0.4ms)"


def test_format_line_no_mock_note():
    line = format_log_line(NOW, "POST", "/nowhere", 404, 0.44, note="no mock")
    assert line == "[2026-09-25 18:05:01] POST /nowhere -> 404 (no mock) (0.4ms)"


def test_format_line_method_not_allowed_note():
    line = format_log_line(NOW, "DELETE", "/api/user", 405, 1.0, note="method not allowed")
    assert line == "[2026-09-25 18:05:01] DELETE /api/user -> 405 (method not allowed) (1.0ms)"


def test_request_log_writes_to_injected_sink():
    sink = io.StringIO()
    RequestLog(sink).log("GET", "/", 200, 1.0)
    assert "-> 200 (1.0ms)" in sink.getvalue()
    assert sink.getvalue().startswith("[")
