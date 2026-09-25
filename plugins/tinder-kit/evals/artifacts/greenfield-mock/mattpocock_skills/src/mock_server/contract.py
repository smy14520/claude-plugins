"""契约（mocks.json）的加载、校验与内存表示。

契约在启动时一次性读入（契约快照）：这里是唯一做 JSON 解析与校验的地方，
之后服务器只查 `Contract.lookup`，不再碰文件。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JSON_CONTENT_TYPE = "application/json; charset=utf-8"
NO_BODY_STATUSES = frozenset({204, 304})
_ALLOWED_ROUTE_KEYS = frozenset({"method", "path", "status", "body"})


class ContractError(Exception):
    """契约文件缺失、不是合法 JSON 或违反校验规则；由 CLI 转成一行人话 + exit 1。"""


@dataclass(frozen=True)
class Route:
    """一条静态路由：method+path 的组合映射到一个固定的模拟响应。"""

    method: str
    path: str
    status: int
    body: bytes  # 启动时序列化好的 JSON 字节，请求期零解析
    has_body: bool

    @property
    def key(self) -> tuple[str, str]:
        return (self.method, self.path)


@dataclass(frozen=True)
class Contract:
    """契约快照：路由列表 + (method, path) -> Route 的精确查找表。"""

    routes: tuple[Route, ...]
    lookup: dict[tuple[str, str], Route]


def load_contract(path: Path) -> Contract:
    """读取并校验契约文件；任何问题都以 ContractError 抛出（启动即失败）。"""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ContractError(f"找不到契约文件 {path}") from None
    except OSError as exc:
        raise ContractError(f"无法读取契约文件 {path}: {exc.strerror}") from None

    document = _parse_json(raw, Path(path))

    if not isinstance(document, dict):
        raise ContractError(f'{path}: 契约顶层必须是对象，形如 {{"routes": [...]}}')
    if "routes" not in document:
        raise ContractError(f'{path}: 缺少 "routes" 字段')
    entries = document["routes"]
    if not isinstance(entries, list):
        raise ContractError(f'{path}: "routes" 必须是数组')

    routes = tuple(
        _build_route(Path(path), index, entry) for index, entry in enumerate(entries, start=1)
    )
    lookup: dict[tuple[str, str], Route] = {}
    for route in routes:
        if route.key in lookup:
            raise ContractError(
                f"{path}: 重复的路由 {route.method} {route.path}，同一路由只能声明一次"
            )
        lookup[route.key] = route
    return Contract(routes=routes, lookup=lookup)


def _parse_json(raw: str, path: Path) -> Any:
    try:
        return json.loads(raw, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"{path}: 不是合法 JSON（第 {exc.lineno} 行第 {exc.colno} 列: {exc.msg}）"
        ) from exc
    except ValueError as exc:  # NaN / Infinity 等非标准 JSON 常量
        raise ContractError(f"{path}: 不是合法 JSON（{exc}）") from exc


def _reject_constant(name: str) -> None:
    raise ValueError(f"{name} 不是合法的 JSON 常量")


def _build_route(path: Path, position: int, entry: Any) -> Route:
    where = f"{path}: 第 {position} 条路由"
    if not isinstance(entry, dict):
        raise ContractError(f"{where} 必须是对象")
    unknown = sorted(set(entry) - _ALLOWED_ROUTE_KEYS)
    if unknown:
        allowed = ", ".join(sorted(_ALLOWED_ROUTE_KEYS))
        raise ContractError(f"{where} 含未知字段 {unknown[0]!r}，允许的字段: {allowed}")
    method = entry.get("method")
    if not isinstance(method, str) or not method.strip():
        raise ContractError(f'{where} 缺少有效的 "method" 字符串')
    route_path = entry.get("path")
    if not isinstance(route_path, str) or not route_path.startswith("/"):
        raise ContractError(f'{where} 的 "path" 必须是以 / 开头的字符串')
    status = entry.get("status", 200)
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
        raise ContractError(f'{where} 的 "status" 必须是 100-599 的整数，收到 {status!r}')
    has_body = "body" in entry
    if has_body and status in NO_BODY_STATUSES:
        raise ContractError(f'{where} 的 status={status} 不允许携带响应体，请删去 "body" 字段')
    body = json.dumps(entry["body"], ensure_ascii=False).encode("utf-8") if has_body else b""
    return Route(
        method=method.strip().upper(),
        path=route_path,
        status=status,
        body=body,
        has_body=has_body,
    )
