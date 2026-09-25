"""契约 seam 的公共行为：加载、全量校验（ADR-0002/0003）与匹配语义（ADR-0004）。"""

import pytest

from mock_server.contract import ContractValidationError, load_contract

# --- 加载与默认值 ---


def test_minimal_route_gets_defaults(write_contract):
    contract = load_contract(write_contract({"routes": [{"path": "/api/user", "body": {"id": 1}}]}))
    (route,) = contract.routes
    assert route.method == "GET"
    assert route.path == "/api/user"
    assert route.status == 200
    assert route.body == {"id": 1}
    assert route.headers == {}


def test_route_fields_are_preserved(write_contract):
    contract = load_contract(
        write_contract(
            {
                "routes": [
                    {
                        "method": "post",
                        "path": "/api/session",
                        "status": 201,
                        "body": {"token": "abc"},
                        "headers": {"X-Trace": "t1"},
                    },
                    {"path": "/api/items", "body": [1, 2]},
                    {"path": "/api/note", "body": "plain text"},
                    {"path": "/api/empty"},
                ]
            },
        )
    )
    post, items, note, empty = contract.routes
    assert post.method == "POST"
    assert post.status == 201
    assert post.headers == {"X-Trace": "t1"}
    assert items.body == [1, 2]
    assert note.body == "plain text"
    assert empty.body is None
    assert empty.status == 200


def test_empty_routes_is_a_valid_contract(write_contract):
    contract = load_contract(write_contract({"routes": []}))
    assert contract.routes == ()


# --- fail-fast 全量校验（ADR-0002）---


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_contract(tmp_path / "nope.json")


def test_invalid_json_is_a_contract_error(tmp_path):
    path = tmp_path / "mocks.json"
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(path)
    assert "invalid JSON" in excinfo.value.errors[0]


def test_root_must_be_an_object(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract([]))
    assert "JSON object" in excinfo.value.errors[0]


def test_routes_key_is_required_and_must_be_a_list(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"nope": []}))
    assert '"routes"' in excinfo.value.errors[0]

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": "all"}))
    assert '"routes"' in excinfo.value.errors[0]


def test_route_must_be_an_object(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": ["GET /api/user"]}))
    assert "route 1" in excinfo.value.errors[0]


def test_path_is_required_and_must_look_like_a_path(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": [{"body": {}}]}))
    assert "path" in excinfo.value.errors[0]

    with pytest.raises(ContractValidationError):
        load_contract(write_contract({"routes": [{"path": "api/user"}]}))


def test_unsupported_method_is_rejected(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": [{"method": "FETCH", "path": "/x"}]}))
    assert "FETCH" in excinfo.value.errors[0]


def test_status_must_be_an_int_in_range(write_contract):
    for bad in [99, 600, "200", True]:
        with pytest.raises(ContractValidationError):
            load_contract(write_contract({"routes": [{"path": "/x", "status": bad}]}))


def test_body_must_be_object_array_string_or_null(write_contract):
    for bad in [42, 1.5, False]:
        with pytest.raises(ContractValidationError) as excinfo:
            load_contract(write_contract({"routes": [{"path": "/x", "body": bad}]}))
    assert "body" in excinfo.value.errors[0]


def test_headers_must_map_names_to_strings(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": [{"path": "/x", "headers": []}]}))
    assert "headers" in excinfo.value.errors[0]

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": [{"path": "/x", "headers": {"X-N": 7}}]}))
    assert "headers" in excinfo.value.errors[0]


def test_unknown_route_field_is_rejected(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(write_contract({"routes": [{"path": "/x", "statu": 500}]}))
    assert "statu" in excinfo.value.errors[0]


def test_duplicate_method_path_is_a_contract_error(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(
            write_contract(
                {
                    "routes": [
                        {"path": "/api/user", "body": {"v": 1}},
                        {"method": "GET", "path": "/api/user", "body": {"v": 2}},
                    ]
                },
            )
        )
    assert any("duplicate" in e for e in excinfo.value.errors)


def test_all_errors_are_collected_not_just_the_first(write_contract):
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(
            write_contract(
                {"routes": [{"method": "FETCH", "path": "bad"}, {"status": 99, "body": 42}]},
            )
        )
    assert len(excinfo.value.errors) >= 3


# --- 匹配语义（ADR-0004）---


@pytest.fixture()
def contract(write_contract):
    return load_contract(
        write_contract(
            {
                "routes": [
                    {"path": "/api/user", "body": {"id": 1}},
                    {"method": "POST", "path": "/api/user", "status": 201},
                ]
            },
        )
    )


def test_exact_match(contract):
    route = contract.match("GET", "/api/user")
    assert route is not None
    assert route.body == {"id": 1}


def test_query_string_is_stripped_before_matching(contract):
    assert contract.match("GET", "/api/user?page=2&full=true") is contract.routes[0]


def test_path_matching_is_case_sensitive(contract):
    assert contract.match("GET", "/API/user") is None


def test_trailing_slash_is_a_different_path(contract):
    assert contract.match("GET", "/api/user/") is None


def test_method_matching_is_case_insensitive(contract):
    assert contract.match("get", "/api/user") is contract.routes[0]
    assert contract.match("PoSt", "/api/user") is contract.routes[1]


def test_method_mismatch_is_a_miss(contract):
    assert contract.match("DELETE", "/api/user") is None
