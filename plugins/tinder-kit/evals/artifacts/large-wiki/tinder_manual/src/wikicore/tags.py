"""行内 #tag 词法：排除 heading、代码围栏与行内代码（Q12）。"""

from __future__ import annotations

import re

from .prose import prose_lines

# `#` 前不能是文字字符或 `/`；标签字符 = Unicode 文字字符 + `-` + `/`，首字符必须是文字字符
_TAG_RE = re.compile(r"(?<![\w/])#(\w[\w/-]*)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")


def extract_inline_tags(body: str) -> list[str]:
    """提取行内标签：小写归一、页内去重保序（一致性裁定 ②）。"""
    tags: list[str] = []
    seen: set[str] = set()
    for line in prose_lines(body):
        if _HEADING_RE.match(line):
            continue
        for match in _TAG_RE.finditer(line):
            tag = match.group(1).lower()
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags
