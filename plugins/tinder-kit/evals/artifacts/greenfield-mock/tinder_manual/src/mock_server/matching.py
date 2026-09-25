"""路由匹配：纯函数，不接触任何 I/O，是 mock-server 匹配语义的唯一实现处。

语义（spec §2）：忽略 query string；尾斜杠严格区分；method 大小写不敏感；
同 path+method 重复声明时先声明者优先（first-wins）。
"""

from __future__ import annotations

from dataclasses import dataclass

from .contract import Route


@dataclass(frozen=True)
class Matched:
    """命中一条路由。"""

    route: Route


@dataclass(frozen=True)
class MethodNotAllowed:
    """路径命中但方法不符：应返回 405，并携带 Allow 头的方法列表。"""

    allowed: tuple[str, ...]


@dataclass(frozen=True)
class NotFound:
    """没有任何路由声明该路径：应返回 404。"""


def strip_query(target: str) -> str:
    """去掉请求目标中的 query string（``?`` 及其后内容）。"""
    return target.split("?", 1)[0]


def match_route(routes: tuple[Route, ...], method: str, target: str) -> Matched | MethodNotAllowed | NotFound:
    """按契约顺序匹配一个请求。"""
    path = strip_query(target)
    wanted = method.upper()
    candidates = [route for route in routes if route.path == path]
    if not candidates:
        return NotFound()
    for route in candidates:
        if route.method.upper() == wanted:
            return Matched(route)
    return MethodNotAllowed(allowed=tuple(dict.fromkeys(route.method for route in candidates)))
