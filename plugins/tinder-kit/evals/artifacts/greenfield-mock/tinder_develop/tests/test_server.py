"""HTTP 服务 seam 的公共行为：响应渲染、未命中语义、访问日志与协议正确性。"""

import http.client
import json
import re
import urllib.error
import urllib.request


def _request(server, path, method="GET"):
    url = f"http://127.0.0.1:{server.address[1]}{path}"
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


# --- 命中响应渲染 ---


def test_json_route_is_served_with_default_content_type(mock_server):
    server = mock_server([{"path": "/api/user", "body": {"id": 1, "name": "Alice"}}])
    status, headers, body = _request(server, "/api/user")
    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert json.loads(body) == {"id": 1, "name": "Alice"}


def test_non_ascii_json_is_served_as_utf8(mock_server):
    server = mock_server([{"path": "/api/user", "body": {"名字": "爱丽丝"}}])
    _, headers, body = _request(server, "/api/user")
    assert "爱丽丝" in body.decode("utf-8")
    assert "charset=utf-8" in headers["Content-Type"]


def test_explicit_headers_are_applied_and_can_override_content_type(mock_server):
    server = mock_server(
        [
            {
                "path": "/api/user",
                "body": {"id": 1},
                "headers": {"X-Foo": "bar", "Content-Type": "application/vnd.api+json"},
            }
        ]
    )
    _, headers, _ = _request(server, "/api/user")
    assert headers["X-Foo"] == "bar"
    assert headers["Content-Type"] == "application/vnd.api+json"


def test_string_body_is_served_as_plain_text(mock_server):
    server = mock_server([{"path": "/api/note", "body": "hello world"}])
    status, headers, body = _request(server, "/api/note")
    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert body == b"hello world"


def test_bodyless_route_serves_an_empty_body(mock_server):
    server = mock_server([{"path": "/api/ping"}])
    status, headers, body = _request(server, "/api/ping")
    assert status == 200
    assert body == b""
    assert headers["Content-Length"] == "0"
    assert "Content-Type" not in headers


def test_route_status_is_used(mock_server):
    server = mock_server([{"method": "POST", "path": "/api/session", "status": 201}])
    status, _, _ = _request(server, "/api/session", method="POST")
    assert status == 201


# --- 未命中语义（ADR-0004）---


def test_miss_answers_404_with_json_error_body(mock_server):
    server = mock_server([{"path": "/api/user", "body": {}}])
    status, headers, body = _request(server, "/api/missing")
    assert status == 404
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert json.loads(body) == {"error": "No mock for GET /api/missing"}


def test_method_mismatch_is_a_miss(mock_server):
    server = mock_server([{"path": "/api/user", "body": {}}])
    status, _, body = _request(server, "/api/user", method="DELETE")
    assert status == 404
    assert json.loads(body) == {"error": "No mock for DELETE /api/user"}


def test_query_string_still_hits(mock_server):
    server = mock_server([{"path": "/api/user", "body": {"id": 1}}])
    status, _, body = _request(server, "/api/user?page=2")
    assert status == 200
    assert json.loads(body) == {"id": 1}


def test_method_outside_whitelist_still_answers_404_json(mock_server):
    # ADR-0004：未命中一律 404 + JSON，绝不许 stdlib 的 501 + HTML 兜底漏出
    server = mock_server([{"path": "/api/user", "body": {}}])
    connection = http.client.HTTPConnection("127.0.0.1", server.address[1])
    connection.request("PROPFIND", "/api/never-mocked")
    response = connection.getresponse()
    assert response.status == 404
    assert json.loads(response.read()) == {"error": "No mock for PROPFIND /api/never-mocked"}
    connection.close()


# --- 协议正确性（ADR-0001 的代价）---


def test_head_returns_headers_without_body(mock_server):
    # HEAD 与 GET 是不同 method（ADR-0004 精确匹配），契约必须显式声明才可被 HEAD 命中
    server = mock_server(
        [
            {"path": "/api/user", "body": {"id": 1}},
            {"method": "HEAD", "path": "/api/user", "body": {"id": 1}},
        ]
    )
    connection = http.client.HTTPConnection("127.0.0.1", server.address[1])
    connection.request("HEAD", "/api/user")
    response = connection.getresponse()
    assert response.status == 200
    assert response.headers["Content-Length"] == str(len(b'{"id": 1}'))
    assert response.read() == b""
    connection.close()


def test_request_body_is_drained_so_keep_alive_connections_survive(mock_server):
    server = mock_server([{"method": "POST", "path": "/api/session", "status": 201}])
    connection = http.client.HTTPConnection("127.0.0.1", server.address[1])
    for sequence in ("one", "two"):
        connection.request(
            "POST",
            "/api/session",
            body=json.dumps({"n": sequence}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 201
        response.read()
    connection.close()


# --- 访问日志（Access Log）---


def test_access_log_records_hits_with_route_pointer(mock_server):
    sink = []
    server = mock_server([{"path": "/api/user", "body": {}}], log=sink.append)
    _request(server, "/api/user?page=2")
    (line,) = sink
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} 127\.0\.0\.1 \"GET /api/user\?page=2\" -> 200 via GET /api/user",
        line,
    )


def test_access_log_records_misses_without_route_pointer(mock_server):
    sink = []
    server = mock_server([{"path": "/api/user", "body": {}}], log=sink.append)
    _request(server, "/api/missing")
    (line,) = sink
    assert "-> 404" in line
    assert " via " not in line
    assert "No mock" not in line
