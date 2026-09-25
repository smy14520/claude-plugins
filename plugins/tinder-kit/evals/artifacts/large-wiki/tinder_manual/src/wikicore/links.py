"""[[链接]] 解析：别名取目标、锚点剥离到页面级（Q10/Q11）。"""

from __future__ import annotations

import re

from .prose import prose_lines

_WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")


def extract_link_targets(body: str) -> list[str]:
    """提取页面级出链目标：丢弃显示名与锚点、跳过自锚点、页内去重保序。"""
    targets: list[str] = []
    seen: set[str] = set()
    for line in prose_lines(body):
        for match in _WIKILINK_RE.finditer(line):
            target = match.group(1).split("|", 1)[0]  # 别名：仅取显示文本之前
            target = target.split("#", 1)[0].strip()  # 锚点/块引用：剥离到页面级
            if not target or target in seen:
                continue  # [[#标题]] 自身锚点不是页面链接
            seen.add(target)
            targets.append(target)
    return targets
