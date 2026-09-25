"""契约文件（mocks.json）的加载与校验。

契约文件是 mock-server 的唯一输入。本模块把 JSON 文本解析并校验为
:class:`Contract`；所有问题（含 JSON 语法错误）都收集为 :class:`ContractError`
列表一次性抛出，由调用方决定消费方式——``serve`` fail-fast，``check`` 全量列出。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

#: 契约中允许声明的 HTTP 方法（必须大写存储）。
KNOWN_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")

_TOP_LEVEL_KEYS = frozenset({"routes", "settings"})
_ROUTE_KEYS = frozenset({"method", "path", "status", "body", "headers"})
_SETTINGS_KEYS = frozenset({"not_found_body"})


@dataclass(frozen=True)
class Route:
    """一条静态路由：method + path 到预置响应的映射。"""

    method: str
    path: str
    status: int
    body: object = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Contract:
    """一份完整契约：有序路由列表与全局设置。"""

    routes: tuple[Route, ...]
    not_found_body: object = None


@dataclass(frozen=True)
class ContractError:
    """契约中一处具体问题，定位精确到 ``routes[N].field`` 或 ``settings.<key>``。"""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


class ContractInvalid(Exception):
    """契约校验失败；``errors`` 携带收集到的全部错误。"""

    def __init__(self, errors: list[ContractError]) -> None:
        self.errors = errors
        super().__init__(f"契约存在 {len(errors)} 处错误")


class ContractFileMissing(Exception):
    """契约文件不存在。"""


def parse_contract(text: str) -> Contract:
    """把契约 JSON 文本解析为 :class:`Contract`。

    任何问题都以 :class:`ContractInvalid` 抛出，且一次携带**全部**错误。
    """
    errors: list[ContractError] = []
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractInvalid(
            [ContractError("mocks.json", f"第 {exc.lineno} 行第 {exc.colno} 列 JSON 解析失败：{exc.msg}")]
        ) from exc

    if not isinstance(doc, dict):
        raise ContractInvalid([ContractError("mocks.json", f"顶层必须是 JSON 对象，实际为 {_type_name(doc)}")])

    for key in sorted(doc):
        if key not in _TOP_LEVEL_KEYS:
            errors.append(ContractError(key, f"未知顶层键（允许：{'、'.join(sorted(_TOP_LEVEL_KEYS))}）"))

    routes: list[Route] = []
    routes_doc = doc.get("routes")
    if routes_doc is None:
        errors.append(ContractError("routes", "缺少必需的顶层键 routes"))
    elif not isinstance(routes_doc, list):
        errors.append(ContractError("routes", f"必须是数组，实际为 {_type_name(routes_doc)}"))
    else:
        routes = _parse_routes(routes_doc, errors)

    not_found_body: object = None
    settings_doc = doc.get("settings")
    if settings_doc is not None:
        if not isinstance(settings_doc, dict):
            errors.append(ContractError("settings", f"必须是对象，实际为 {_type_name(settings_doc)}"))
        else:
            for key in sorted(settings_doc):
                if key not in _SETTINGS_KEYS:
                    errors.append(
                        ContractError(f"settings.{key}", f"未知设置键（允许：{'、'.join(sorted(_SETTINGS_KEYS))}）")
                    )
            not_found_body = settings_doc.get("not_found_body")

    if errors:
        raise ContractInvalid(errors)
    return Contract(routes=tuple(routes), not_found_body=not_found_body)


def load_contract_file(path: str) -> Contract:
    """读取并解析契约文件；文件不存在抛 :class:`ContractFileMissing`。"""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContractFileMissing(str(path)) from exc
    return parse_contract(text)


def _parse_routes(routes_doc: list[object], errors: list[ContractError]) -> list[Route]:
    routes: list[Route] = []
    for index, item in enumerate(routes_doc):
        where = f"routes[{index}]"
        if not isinstance(item, dict):
            errors.append(ContractError(where, f"必须是对象，实际为 {_type_name(item)}"))
            continue
        for key in sorted(item):
            if key not in _ROUTE_KEYS:
                errors.append(
                    ContractError(f"{where}.{key}", f"未知路由字段（允许：{'、'.join(sorted(_ROUTE_KEYS))}）")
                )

        method = item.get("method")
        if not (isinstance(method, str) and method in KNOWN_METHODS):
            errors.append(
                ContractError(
                    f"{where}.method",
                    f"必须是合法的大写 HTTP 方法（{'/'.join(KNOWN_METHODS)}），实际为 {method!r}",
                )
            )

        path = item.get("path")
        if not (isinstance(path, str) and path.startswith("/")):
            errors.append(ContractError(f"{where}.path", f"必须是以 / 开头的字符串，实际为 {path!r}"))
        elif "?" in path:
            errors.append(ContractError(f"{where}.path", "路径中不应包含 ?（匹配器忽略 query），请只写路径部分"))

        status = item.get("status")
        if isinstance(status, bool) or not isinstance(status, int):
            errors.append(ContractError(f"{where}.status", f"必须是 100~599 的整数，实际为 {status!r}"))
        elif not 100 <= status <= 599:
            errors.append(ContractError(f"{where}.status", f"必须是 100~599 的整数，实际为 {status}"))

        headers_doc = item.get("headers")
        if headers_doc is not None and not (
            isinstance(headers_doc, dict)
            and all(isinstance(k, str) and isinstance(v, str) for k, v in headers_doc.items())
        ):
            errors.append(ContractError(f"{where}.headers", "必须是字符串到字符串的对象"))

        routes.append(
            Route(
                method=method if isinstance(method, str) else "",
                path=path if isinstance(path, str) else "",
                status=status if isinstance(status, int) and not isinstance(status, bool) else 0,
                body=item.get("body"),
                headers=dict(headers_doc) if isinstance(headers_doc, dict) else {},
            )
        )
    return routes


def _type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "布尔值"
    if isinstance(value, (int, float)):
        return "数字"
    if isinstance(value, str):
        return "字符串"
    if isinstance(value, list):
        return "数组"
    if isinstance(value, dict):
        return "对象"
    return type(value).__name__
