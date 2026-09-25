"""契约（Contract）的加载、校验与匹配。

契约是 mocks.json 文件整体：路由的集合，是 mock server 全部行为的最小且唯一的
配置来源（见 .forge/CONTEXT.md「契约」）。加载遵循 ADR-0002：启动时一次性读取
并全量校验，收集所有错误后一次性报告；匹配遵循 ADR-0004：精确匹配，未命中由
HTTP 层以 404 应答。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE")
ALLOWED_ROUTE_FIELDS = ("method", "path", "status", "body", "headers")


class ContractValidationError(Exception):
    """契约校验失败。errors 按契约顺序收集全部问题，而非首错即停（ADR-0002）。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class Route:
    """契约中的一条模拟规则：method、path、status、body、headers 五要素。"""

    method: str
    path: str
    status: int
    body: object = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Contract:
    """一组无歧义的路由（ADR-0003：method+path 重复即契约错误）。"""

    routes: tuple[Route, ...]

    def match(self, method: str, path: str) -> Route | None:
        """命中：method 大小写不敏感；path 剥离 query string 后逐字符相等。"""
        clean = strip_query(path)
        wanted = method.upper()
        for route in self.routes:
            if route.method == wanted and route.path == clean:
                return route
        return None


def strip_query(path: str) -> str:
    """命中规则的唯一权威实现：剥离 query string（ADR-0004）。"""
    return path.split("?", 1)[0]


def load_contract(path: str | Path) -> Contract:
    """读取并校验契约文件；失败抛 ContractValidationError，错误全量收集。"""
    raw = Path(path).read_text(encoding="utf-8")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractValidationError([f"invalid JSON: {exc}"]) from exc
    errors: list[str] = []
    routes = _validate_document(document, errors)
    if errors:
        raise ContractValidationError(errors)
    return Contract(routes=tuple(routes))


def _validate_document(document: object, errors: list[str]) -> list[Route]:
    routes: list[Route] = []
    if not isinstance(document, dict):
        errors.append("contract root must be a JSON object")
        return routes
    entries = document.get("routes")
    if not isinstance(entries, list):
        errors.append('contract must contain a "routes" array')
        return routes

    seen: set[tuple[str, str]] = set()
    for index, raw_route in enumerate(entries, start=1):
        route = _validate_route(index, raw_route, errors)
        if route is None:
            continue
        key = (route.method, route.path)
        if key in seen:
            errors.append(f"route {index} ({route.method} {route.path}): duplicate route")
            continue
        seen.add(key)
        routes.append(route)
    return routes


def _validate_route(index: int, raw_route: object, errors: list[str]) -> Route | None:
    if not isinstance(raw_route, dict):
        errors.append(f"route {index}: must be a JSON object")
        return None

    where = f"route {index} ({_route_label(raw_route)})"
    start = len(errors)

    unknown = sorted(set(raw_route) - set(ALLOWED_ROUTE_FIELDS))
    if unknown:
        errors.append(f"{where}: unknown field(s) {', '.join(unknown)}")

    method = "GET"
    raw_method = raw_route.get("method", "GET")
    if not isinstance(raw_method, str):
        errors.append(f"{where}: method must be a string")
    else:
        method = raw_method.upper()
        if method not in ALLOWED_METHODS:
            errors.append(f"{where}: unsupported method {raw_method!r}")

    path = None
    raw_path = raw_route.get("path")
    if not isinstance(raw_path, str) or not raw_path.startswith("/"):
        errors.append(f"{where}: path is required and must be a string starting with '/'")
    else:
        path = raw_path

    status = 200
    raw_status = raw_route.get("status", 200)
    if isinstance(raw_status, bool) or not isinstance(raw_status, int) or not 200 <= raw_status <= 599:
        errors.append(f"{where}: status must be an integer in 200..599")
    else:
        status = raw_status

    body: object = None
    if "body" in raw_route:
        raw_body = raw_route["body"]
        if isinstance(raw_body, (dict, list, str)) or raw_body is None:
            body = raw_body
        else:
            errors.append(f"{where}: body must be a JSON object, array, string, or null")

    headers: dict[str, str] = {}
    raw_headers = raw_route.get("headers", {})
    if not isinstance(raw_headers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in raw_headers.items()
    ):
        errors.append(f"{where}: headers must be an object mapping names to strings")
    else:
        headers = dict(raw_headers)

    if len(errors) > start:
        return None
    return Route(method=method, path=path, status=status, body=body, headers=headers)


def _route_label(raw_route: dict) -> str:
    method = raw_route.get("method", "GET")
    path = raw_route.get("path", "?")
    method_text = method if isinstance(method, str) else "?"
    path_text = path if isinstance(path, str) else "?"
    return f"{method_text} {path_text}"
