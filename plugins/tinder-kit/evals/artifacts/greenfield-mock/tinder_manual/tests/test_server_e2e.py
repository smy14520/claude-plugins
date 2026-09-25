"""HTTP 服务层端到端测试：真实 ThreadingHTTPServer 绑定 port 0 后台线程 + urllib 请求。

无固定端口依赖（内核分配），无网络抖动（仅回环）。
"""

import io
import json
import threading
import urllib.error
import urllib.request

import pytest

from mock_server.contract import parse_contract
from mock_server.server import make_server

CONTRACT = """
{
  "settings": { "not_found_body": { "error": "custom-not-found" } },
  "routes": [
    { "method": "GET", "path": "/api/user", "status": 200, "body": {"id": 1} },
    { "method": "GET", "path": "/api/plain", "status": 200, "body": "hello",
      "headers": {"Content-Type": "text/plain; charset=utf-8", "X-Flag": "v"} },
    { "method": "POST", "path": "/api/echo", "status": 201, "body": {"created": true} },
    { "method": "DELETE", "path": "/api/empty", "status": 204 },
    { "method": "GET", "path": "/api/dup", "status": 200, "body": "first" },
    { "method": "GET", "path": "/api/dup", "status": 200, "body": "second" }
  ]
}
"""

BARE_CONTRACT = """
{ "routes": [ { "method": "GET", "path": "/api/user", "status": 200, "body": {"id": 1} } ] }
"""


@pytest.fixture
def start_server():
    servers: list[object] = []

    def _start(contract_json: str) -> tuple[str, io.StringIO]:
        sink = io.StringIO()
        server = make_server(parse_contract(contract_json), host="127.0.0.1", port=0, sink=sink)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}", sink

    yield _start
    for server in servers:
        server.shutdown()
        server.server_close()


def request(method: str, url: str, data: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read()


def test_hit_route_returns_canned_json(start_server):
    base, _ = start_server(CONTRACT)
    status, headers, body = request("GET", f"{base}/api/user")
    assert status == 200
    assert json.loads(body) == {"id": 1}
    assert headers["Content-Type"] == "application/json"


def test_query_string_is_ignored(start_server):
    base, _ = start_server(CONTRACT)
    status, _, _ = request("GET", f"{base}/api/user?page=2&size=10")
    assert status == 200


def test_trailing_slash_is_404_with_settings_body(start_server):
    base, _ = start_server(CONTRACT)
    status, headers, body = request("GET", f"{base}/api/user/")
    assert status == 404
    assert json.loads(body) == {"error": "custom-not-found"}
    assert headers["Content-Type"] == "application/json"


def test_default_not_found_body(start_server):
    base, _ = start_server(BARE_CONTRACT)
    status, _, body = request("GET", f"{base}/nowhere")
    assert status == 404
    assert json.loads(body) == {"error": "no mock for GET /nowhere"}


def test_method_not_allowed_with_allow_header(start_server):
    base, _ = start_server(BARE_CONTRACT)
    status, headers, body = request("POST", f"{base}/api/user")
    assert status == 405
    assert headers["Allow"] == "GET"
    assert json.loads(body) == {"error": "method not allowed for /api/user"}


def test_custom_headers_override_content_type(start_server):
    base, _ = start_server(CONTRACT)
    status, headers, body = request("GET", f"{base}/api/plain")
    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert headers["X-Flag"] == "v"
    assert body == b'"hello"'


HEAD_CONTRACT = """
{ "routes": [ { "method": "HEAD", "path": "/api/user", "status": 200, "body": {"id": 1} } ] }
"""


def test_head_returns_headers_without_body(start_server):
    base, _ = start_server(HEAD_CONTRACT)
    status, headers, body = request("HEAD", f"{base}/api/user")
    assert status == 200
    assert body == b""
    assert headers["Content-Length"] == str(len(json.dumps({"id": 1})))


def test_head_against_get_only_route_is_405(start_server):
    # HEAD 不自动回退到 GET 路由：契约写什么匹配什么（严格语义）。
    base, _ = start_server(BARE_CONTRACT)
    status, _, _ = request("HEAD", f"{base}/api/user")
    assert status == 405


def test_body_absent_means_empty_response_without_content_type(start_server):
    base, _ = start_server(CONTRACT)
    status, headers, body = request("DELETE", f"{base}/api/empty")
    assert status == 204
    assert body == b""
    assert "Content-Type" not in headers


def test_first_duplicate_route_wins(start_server):
    base, _ = start_server(CONTRACT)
    status, _, body = request("GET", f"{base}/api/dup")
    assert status == 200
    assert body == b'"first"'


def test_post_with_body_is_drained_and_answered(start_server):
    base, _ = start_server(CONTRACT)
    status, _, body = request("POST", f"{base}/api/echo", data=json.dumps({"x": 1}).encode("utf-8"))
    assert status == 201
    assert json.loads(body) == {"created": True}


def test_request_log_lines_captured(start_server):
    base, sink = start_server(CONTRACT)
    request("GET", f"{base}/api/user")
    request("GET", f"{base}/api/user/missing")
    lines = [line for line in sink.getvalue().splitlines() if line.strip()]
    assert len(lines) == 2
    assert "-> 200 (" in lines[0] and "GET /api/user " in lines[0]
    assert "-> 404 (no mock)" in lines[1]
