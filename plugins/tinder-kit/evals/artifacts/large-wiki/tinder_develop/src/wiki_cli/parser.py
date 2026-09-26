"""Parser：单文件 Markdown 解析器。

输入一个 .md 文件的文本，输出该页的结构化视图。本层不知道 Vault 里
有哪些页面，不做任何跨文件判断——目标到 Page 的解析由 LinkGraph 负责。

行级状态机 `iter_effective_lines`：跳过围栏代码块（``` 与 ~~~）、剥离行内
代码后逐行产出"有效文本"；Link 提取建立在其上，Tag 提取（tags 工单）同样复用。
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

_FENCE_RE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})")
_WIKILINK_RE = re.compile(r"\[\[(?P<raw>[^\[\]]+)\]\]")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


@dataclass(frozen=True)
class Link:
    """一条 `[[目标]]` 引用；target 为剥离别名与锚点后的目标写法。"""

    target: str
    line: int  # 1 起算的行号


@dataclass
class ParseResult:
    """单页解析产物；后续工单在此扩展 tags 与纯文本正文。"""

    links: list[Link] = field(default_factory=list)


def iter_effective_lines(text: str) -> Iterator[tuple[int, str]]:
    """逐行产出 (行号, 有效文本)。

    围栏代码块内的行整体跳过；围栏开合行不产出；行内代码被剥离。
    """
    fence_char = ""  # 当前所处围栏的标记字符（` 或 ~），空串表示不在围栏内
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        match = _FENCE_RE.match(raw_line)
        if match:
            marker_char = match.group("marker")[0]
            if not fence_char:
                fence_char = marker_char  # 开栏（含信息串）
            elif marker_char == fence_char:
                fence_char = ""  # 闭栏
            # 标记字符不同的行按围栏内容处理
            continue
        if fence_char:
            continue
        yield lineno, _INLINE_CODE_RE.sub("", raw_line)


def parse_link_target(raw: str) -> str | None:
    """归约 `[[...]]` 内部文本：取管道前第一段为目标，再剥离 `#` 锚点。

    剥离后为空（如 `[[#小节]]`、`[[]]`）返回 None，表示没有可解析目标。
    """
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    return target or None


def parse_markdown(text: str) -> ParseResult:
    """解析单页文本，产出全部 Link（含行号，保留文中出现顺序）。"""
    result = ParseResult()
    for lineno, effective_line in iter_effective_lines(text):
        for match in _WIKILINK_RE.finditer(effective_line):
            target = parse_link_target(match.group("raw"))
            if target is not None:
                result.links.append(Link(target=target, line=lineno))
    return result
