"""路由匹配语义的穷举单元测试（纯函数）。"""

from mock_server.contract import Route
from mock_server.matching import (
    Matched,
    MethodNotAllowed,
    NotFound,
    match_route,
    strip_query,
)


def routes(*specs: tuple[str, str]) -> tuple[Route, ...]:
    return tuple(Route(method, path, 200) for method, path in specs)


def test_strip_query():
    assert strip_query("/api/user?page=1&x=2") == "/api/user"
    assert strip_query("/api/user") == "/api/user"
    assert strip_query("/api/user?") == "/api/user"


def test_exact_hit():
    rs = routes(("GET", "/api/user"))
    result = match_route(rs, "GET", "/api/user")
    assert isinstance(result, Matched)
    assert result.route.path == "/api/user"


def test_query_is_ignored():
    rs = routes(("GET", "/api/user"))
    result = match_route(rs, "GET", "/api/user?page=1&size=10")
    assert isinstance(result, Matched)


def test_trailing_slash_is_strict():
    rs = routes(("GET", "/api/user"))
    assert isinstance(match_route(rs, "GET", "/api/user/"), NotFound)
    assert isinstance(match_route(routes(("GET", "/api/user/")), "GET", "/api/user"), NotFound)


def test_method_not_allowed_carries_allowed_set():
    rs = routes(("GET", "/api/user"), ("POST", "/api/user"))
    result = match_route(rs, "DELETE", "/api/user")
    assert isinstance(result, MethodNotAllowed)
    assert result.allowed == ("GET", "POST")


def test_method_case_insensitive():
    rs = routes(("GET", "/api/user"))
    assert isinstance(match_route(rs, "get", "/api/user"), Matched)


def test_first_route_wins_on_duplicates():
    rs = (
        Route("GET", "/a", 200, "first"),
        Route("GET", "/a", 200, "second"),
    )
    result = match_route(rs, "GET", "/a")
    assert isinstance(result, Matched)
    assert result.route.body == "first"


def test_unknown_path_not_found():
    rs = routes(("GET", "/api/user"))
    assert isinstance(match_route(rs, "GET", "/nowhere"), NotFound)


def test_empty_routes_not_found():
    assert isinstance(match_route((), "GET", "/anything"), NotFound)
