"""正文净化：剔除代码围栏与行内代码，供链接与标签扫描共用（一致性裁定 ①）。"""

from __future__ import annotations

import re
from collections.abc import Iterator

_FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_FENCE_CLOSE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*$")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def prose_lines(text: str) -> Iterator[str]:
    """按行产出围栏之外、行内代码已替换为空格的正文行。"""
    fence = ""
    for line in text.splitlines():
        if fence:
            if _FENCE_CLOSE_RE.match(line) and line.lstrip()[0] == fence:
                fence = ""
            continue
        opened = _FENCE_RE.match(line)
        if opened:
            fence = opened.group(1)[0]
            continue
        yield _INLINE_CODE_RE.sub(" ", line)
