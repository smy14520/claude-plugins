"""检索文本处理：统一 token 化（ADR-0003）。

tokenize 规则：文本先 casefold；Latin/数字/下划线连续段为一个词元；
CJK（含假名、兼容表意、谚文）连续段按二元组切分，长度 1 的残段取单字。
检索的执行在 `wikicore.model.Index.search`；摘要渲染属 CLI 层（ADR-0004 修订）。
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(
    r"[0-9a-z_]+|[぀-ヿ㐀-䶿一-鿿豈-﫿가-힯]+"
)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(text.casefold()):
        run = match.group()
        if run[0].isascii():
            tokens.append(run)
        elif len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    return tokens
