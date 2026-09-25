"""契约文件加载与校验的穷举单元测试（纯函数，无 I/O socket）。"""

import json

import pytest

from mock_server.contract import Contract, ContractInvalid, Route, parse_contract


def parse_ok(doc: object) -> Contract:
    return parse_contract(json.dumps(doc))


def errors_of(doc: object) -> list[str]:
    with pytest.raises(ContractInvalid) as excinfo:
        parse_contract(doc if isinstance(doc, str) else json.dumps(doc))
    return [str(err) for err in excinfo.value.errors]


def test_minimal_valid_contract():
    contract = parse_ok({"routes": [{"method": "GET", "path": "/api/user", "status": 200, "body": {"id": 1}}]})
    assert contract.routes == (Route("GET", "/api/user", 200, {"id": 1}, {}),)
    assert contract.not_found_body is None


def test_defaults_body_headers_settings():
    contract = parse_ok({"routes": [{"method": "POST", "path": "/api/x", "status": 201}]})
    assert contract.routes == (Route("POST", "/api/x", 201, None, {}),)


def test_settings_not_found_body_accepted():
    body = {"error": "custom"}
    contract = parse_ok({"settings": {"not_found_body": body}, "routes": []})
    assert contract.not_found_body == body


def test_json_syntax_error():
    errs = errors_of("{not json")
    assert len(errs) == 1
    assert "JSON 解析失败" in errs[0]
    assert "第 1 行" in errs[0]


def test_top_level_not_object():
    errs = errors_of([1, 2])
    assert "顶层必须是 JSON 对象" in errs[0]


def test_missing_routes_key():
    errs = errors_of({"settings": {}})
    assert any("routes" in e and "缺少" in e for e in errs)


def test_routes_not_array():
    errs = errors_of({"routes": "nope"})
    assert "routes: 必须是数组" in errs[0]


def test_unknown_top_level_key():
    errs = errors_of({"route": [], "routes": []})
    assert any("route" in e and "未知顶层键" in e for e in errs)


def test_unknown_settings_key():
    errs = errors_of({"settings": {"not_found": 1}, "routes": []})
    assert any("settings.not_found" in e and "未知设置键" in e for e in errs)


def test_unknown_route_field():
    errs = errors_of({"routes": [{"method": "GET", "path": "/a", "status": 200, "statue": 1}]})
    assert any("statue" in e and "未知路由字段" in e for e in errs)


def test_route_not_object():
    errs = errors_of({"routes": ["GET /a"]})
    assert "routes[0]: 必须是对象" in errs[0]


@pytest.mark.parametrize("method", ["get", "GETT", 200, None])
def test_method_must_be_known_uppercase(method):
    errs = errors_of({"routes": [{"method": method, "path": "/a", "status": 200}]})
    assert any("routes[0].method" in e and "大写" in e for e in errs)


@pytest.mark.parametrize("path", ["api/user", "", 3, None])
def test_path_must_start_with_slash(path):
    errs = errors_of({"routes": [{"method": "GET", "path": path, "status": 200}]})
    assert any("routes[0].path" in e for e in errs)


def test_path_must_not_contain_query():
    errs = errors_of({"routes": [{"method": "GET", "path": "/a?x=1", "status": 200}]})
    assert any("routes[0].path" in e and "?" in e for e in errs)


@pytest.mark.parametrize("status", [True, 99, 600, "200", 2.5, None])
def test_status_must_be_int_in_range(status):
    errs = errors_of({"routes": [{"method": "GET", "path": "/a", "status": status}]})
    assert any("routes[0].status" in e for e in errs)


def test_headers_must_be_string_to_string():
    errs = errors_of({"routes": [{"method": "GET", "path": "/a", "status": 200, "headers": {"X-N": 1}}]})
    assert any("routes[0].headers" in e for e in errs)


def test_all_errors_collected_at_once():
    errs = errors_of(
        {
            "routes": [
                {"method": "get", "path": "bad", "status": 999},
                {"method": "GET", "path": "/ok", "status": 200},
                {"method": "POST", "path": "/also-bad?x", "status": "201"},
            ]
        }
    )
    # routes[0] 三处 + routes[2] 两处，全部一次性列出
    assert any("routes[0].method" in e for e in errs)
    assert any("routes[0].path" in e for e in errs)
    assert any("routes[0].status" in e for e in errs)
    assert any("routes[2].path" in e for e in errs)
    assert any("routes[2].status" in e for e in errs)
    assert not any("routes[1]" in e for e in errs)
