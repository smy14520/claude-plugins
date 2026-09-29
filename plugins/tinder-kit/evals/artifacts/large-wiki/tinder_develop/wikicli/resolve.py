"""resolve：链接目标 × 页面全集 → Resolved | Dead | Ambiguous（三态）。

解析顺序（spec）：含路径则按相对路径精确匹配；否则 stem 精确匹配，
失败后大小写不敏感兜底。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .parse import Page

RESOLVED = "resolved"
DEAD = "dead"
AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class Resolution:
    """一次链接解析的三态结果。"""

    status: str  # RESOLVED / DEAD / AMBIGUOUS
    targets: tuple[Page, ...] = ()  # 命中的候选页面（dead 为空）


def resolve_link(
    target: str,
    by_name: Mapping[str, Sequence[Page]],
    by_path: Mapping[str, Page],
) -> Resolution:
    """按解析顺序把链接目标解析为三态之一。"""
    if "/" in target:  # 路径写法：仅相对路径精确匹配，不进 stem 兜底
        page = by_path.get(target)
        if page is None:
            return Resolution(status=DEAD)
        return Resolution(status=RESOLVED, targets=(page,))
    matches = by_name.get(target, ())
    if len(matches) == 1:
        return Resolution(status=RESOLVED, targets=(matches[0],))
    if len(matches) > 1:
        return Resolution(status=AMBIGUOUS, targets=tuple(matches))
    lowered = target.lower()  # stem 精确匹配失败：大小写不敏感兜底
    fallback = [
        page
        for name, pages in by_name.items()
        if name.lower() == lowered
        for page in pages
    ]
    if len(fallback) == 1:
        return Resolution(status=RESOLVED, targets=(fallback[0],))
    if len(fallback) > 1:
        return Resolution(status=AMBIGUOUS, targets=tuple(fallback))
    return Resolution(status=DEAD)
