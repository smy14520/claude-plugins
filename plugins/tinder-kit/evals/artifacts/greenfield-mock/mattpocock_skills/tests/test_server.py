"""集成测试：真起服务（127.0.0.1:0），用 http.client 打 HTTP，验证匹配规则与响应语义。"""

import json
import time


def test_get_route_returns_contracted_json(server_factory, send):
    payload = {"id": 1, "name": "晶", "email": "jing@example.com"}
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": payload}]})
    response, body = send(base, "GET", "/api/user")
    assert response.status == 200
    assert response.headers["Content-Type"] == "application/json; charset=utf-8"
    assert json.loads(body) == payload


def test_query_string_is_ignored(server_factory, send):
    base = server_factory(
        {"routes": [{"method": "GET", "path": "/api/user", "body": {"ok": True}}]}
    )
    response, _ = send(base, "GET", "/api/user?_=1698888888&trace=1")
    assert response.status == 200


def test_trailing_slash_is_a_miss(server_factory, send):
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": {}}]})
    response, body = send(base, "GET", "/api/user/")
    assert response.status == 404
    assert json.loads(body) == {
        "error": "route not found",
        "method": "GET",
        "path": "/api/user/",
    }


def test_method_mismatch_is_404_not_405(server_factory, send):
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": {}}]})
    response, body = send(base, "POST", "/api/user")
    assert response.status == 404
    assert json.loads(body)["method"] == "POST"


def test_arbitrary_method_is_404_not_501(server_factory, send):
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": {}}]})
    response, body = send(base, "FROBNICATE", "/api/user")
    assert response.status == 404
    assert json.loads(body)["method"] == "FROBNICATE"


def test_same_path_different_methods_are_independent(server_factory, send):
    base = server_factory(
        {
            "routes": [
                {"method": "GET", "path": "/api/user", "status": 200, "body": {"role": "reader"}},
                {"method": "POST", "path": "/api/user", "status": 201, "body": {"created": True}},
            ]
        }
    )
    get_response, get_body = send(base, "GET", "/api/user")
    post_response, post_body = send(base, "POST", "/api/user")
    assert (get_response.status, json.loads(get_body)) == (200, {"role": "reader"})
    assert (post_response.status, json.loads(post_body)) == (201, {"created": True})


def test_head_in_contract_keeps_headers_omits_body(server_factory, send):
    payload = {"session": "closed"}
    base = server_factory({"routes": [{"method": "HEAD", "path": "/api/session", "body": payload}]})
    response, body = send(base, "HEAD", "/api/session")
    assert response.status == 200
    expected = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    assert int(response.headers["Content-Length"]) == expected
    assert body == b""


def test_head_not_in_contract_is_404(server_factory, send):
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": {}}]})
    response, _ = send(base, "HEAD", "/api/user")
    assert response.status == 404


def test_body_omitted_means_empty_body(server_factory, send):
    base = server_factory({"routes": [{"method": "DELETE", "path": "/api/session", "status": 200}]})
    response, body = send(base, "DELETE", "/api/session")
    assert response.status == 200
    assert body == b""
    assert response.headers["Content-Length"] == "0"
    assert "Content-Type" not in response.headers


def test_204_has_no_entity_headers_or_body(server_factory, send):
    base = server_factory({"routes": [{"method": "DELETE", "path": "/api/session", "status": 204}]})
    response, body = send(base, "DELETE", "/api/session")
    assert response.status == 204
    assert body == b""
    assert "Content-Length" not in response.headers
    assert "Content-Type" not in response.headers


def test_access_log_one_line_per_request(server_factory, send, capsys):
    base = server_factory({"routes": [{"method": "GET", "path": "/api/user", "body": {}}]})
    send(base, "GET", "/api/user?x=1")
    send(base, "GET", "/api/usesr")
    time.sleep(0.2)  # 日志在 handler 线程里打，等它落到 stdout
    out = capsys.readouterr().out
    assert "GET /api/user?x=1 → 200 " in out
    assert "GET /api/usesr → 404 " in out
