"""契约加载与校验的全分支单测：启动即失败（fail-fast）的每条规则都有对应用例。"""

import json
from pathlib import Path
from typing import Any

import pytest

from mock_server.contract import ContractError, load_contract


def _load(tmp_path: Path, raw: Any) -> object:
    path = tmp_path / "mocks.json"
    content = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    path.write_text(content, encoding="utf-8")
    return load_contract(path)


def _err(tmp_path: Path, raw: Any) -> str:
    with pytest.raises(ContractError) as excinfo:
        _load(tmp_path, raw)
    return str(excinfo.value)


def test_minimal_route_defaults(tmp_path):
    contract = _load(tmp_path, {"routes": [{"method": "get", "path": "/api/user"}]})
    (route,) = contract.routes
    assert (route.method, route.path, route.status, route.has_body) == (
        "GET",
        "/api/user",
        200,
        False,
    )
    assert route.body == b""
    assert contract.lookup[("GET", "/api/user")] is route


def test_body_is_serialized_once_as_utf8_json(tmp_path):
    contract = _load(
        tmp_path, {"routes": [{"method": "GET", "path": "/p", "body": {"名字": "晶"}}]}
    )
    route = contract.lookup[("GET", "/p")]
    assert route.has_body
    assert json.loads(route.body.decode("utf-8")) == {"名字": "晶"}
    assert "晶".encode() in route.body  # 非转义输出，契约里的数据原样出去


def test_explicit_null_body_is_a_body(tmp_path):
    contract = _load(tmp_path, {"routes": [{"method": "GET", "path": "/p", "body": None}]})
    (route,) = contract.routes
    assert route.has_body
    assert route.body == b"null"


def test_empty_routes_is_a_valid_contract(tmp_path):
    contract = _load(tmp_path, {"routes": []})
    assert contract.routes == ()
    assert contract.lookup == {}


def test_204_without_body_is_allowed(tmp_path):
    contract = _load(tmp_path, {"routes": [{"method": "DELETE", "path": "/s", "status": 204}]})
    assert contract.routes[0].status == 204


@pytest.mark.parametrize("status", [204, 304])
def test_no_body_status_with_body_is_rejected(tmp_path, status):
    message = _err(
        tmp_path, {"routes": [{"method": "GET", "path": "/p", "status": status, "body": {}}]}
    )
    assert "不允许携带响应体" in message


@pytest.mark.parametrize("status", ["200", True, 99, 600, 1.5, None])
def test_invalid_status_is_rejected(tmp_path, status):
    document = {"routes": [{"method": "GET", "path": "/p", "status": status}]}
    assert '"status"' in _err(tmp_path, document)


@pytest.mark.parametrize(
    "bad", [{"path": "/p"}, {"method": "", "path": "/p"}, {"method": "  ", "path": "/p"}]
)
def test_invalid_method_is_rejected(tmp_path, bad):
    assert '"method"' in _err(tmp_path, {"routes": [bad]})


@pytest.mark.parametrize("bad_path", ["api/user", "", 3, None])
def test_invalid_path_is_rejected(tmp_path, bad_path):
    document = {"routes": [{"method": "GET", "path": bad_path}]}
    assert '"path"' in _err(tmp_path, document)


def test_unknown_field_is_rejected_with_hint(tmp_path):
    message = _err(tmp_path, {"routes": [{"method": "GET", "path": "/p", "header": {"X": "y"}}]})
    assert "未知字段" in message
    assert "header" in message


def test_duplicate_route_is_rejected(tmp_path):
    document = {
        "routes": [
            {"method": "GET", "path": "/api/user", "body": {"v": 1}},
            {"method": "GET", "path": "/api/user", "body": {"v": 2}},
        ]
    }
    assert "重复的路由" in _err(tmp_path, document)


def test_top_level_shapes_are_rejected(tmp_path):
    assert "顶层" in _err(tmp_path, [])
    assert "routes" in _err(tmp_path, {"route": []})
    assert "routes" in _err(tmp_path, {"routes": {}})


def test_non_route_entries_are_rejected(tmp_path):
    assert "必须是对象" in _err(tmp_path, {"routes": ["GET /p"]})


def test_missing_file(tmp_path):
    with pytest.raises(ContractError, match="找不到契约文件"):
        load_contract(tmp_path / "nope.json")


def test_broken_json_reports_position(tmp_path):
    assert "不是合法 JSON" in _err(tmp_path, "{oops")


def test_nan_is_not_valid_json(tmp_path):
    message = _err(tmp_path, '{"routes": [{"method": "GET", "path": "/p", "body": {"x": NaN}}]}')
    assert "NaN" in message
