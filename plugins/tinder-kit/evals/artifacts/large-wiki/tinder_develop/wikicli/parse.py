"""parse：文本 → 页面结构（Page）。

本模块产出 Page 数据结构；链接解析（目标能否对应页面）属于 resolve，
这里只负责从文本里提取结构。后续 ticket 会在 `strip_code` 之上加标签提取。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

#: 链接形态：`[[目标]]`、`[[目标|别名]]`（锚点剥离在后续 ticket）
_LINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


@dataclass(frozen=True)
class Link:
    """一个链接出现处。"""

    raw: str  # 双括号内原文，如 `python|Py 学习笔记`
    target: str  # 剥离别名后的解析目标（页面名或路径写法）
    line: int  # 1 起的行号（供反向引用等后续 ticket 使用）


@dataclass(frozen=True)
class Page:
    """vault 内一个 `.md` 文件的结构化视图。"""

    path: str  # vault 相对路径（posix 分隔）
    name: str  # 页面名 = 文件名 stem
    links: tuple[Link, ...] = ()
    title: str | None = None  # frontmatter `title:`；无 frontmatter 时为 None
    tags: tuple[str, ...] = ()  # 正文标签 + frontmatter `tags:` 并入（去重保序）


def strip_code(text: str) -> str:
    """剥离围栏代码块与行内代码，返回仅用于提取的替身文本。

    独立共用函数：链接提取与后续的标签提取都必须先过这里，
    保证"代码区内容不产生任何链接或标签"只有一份实现。
    换行位置原样保留（每行内容替换为等长空格），行号信息不受影响。
    """
    return _strip_inline_code(_strip_fenced_blocks(text))


_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _strip_fenced_blocks(text: str) -> str:
    """清空围栏代码块内容；换行结构保留，行号不漂移。"""
    lines = text.split("\n")
    out: list[str] = []
    inside = False
    fence_char = ""
    fence_len = 0
    for line in lines:
        if not inside:
            match = _FENCE_OPEN_RE.match(line)
            if match:
                inside = True
                fence_char = match.group(1)[0]
                fence_len = len(match.group(1))
                out.append("")
            else:
                out.append(line)
        else:
            stripped = line.strip()
            if stripped and set(stripped) == {fence_char} and len(stripped) >= fence_len:
                inside = False  # 闭合围栏：至少等长、同字符、无其他内容
            out.append("")
    return "\n".join(out)


_INLINE_CODE_RE = re.compile(r"`+[^`]*`+")


def _strip_inline_code(text: str) -> str:
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)


def extract_links(text: str) -> tuple[Link, ...]:
    """从已剥离代码区的正文提取链接（按出现顺序）。"""
    links = []
    for match in _LINK_RE.finditer(text):
        raw = match.group(1)
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            continue  # `[[#小节]]` 页内锚：无页面部分，整体跳过
        line = text.count("\n", 0, match.start()) + 1
        links.append(Link(raw=raw, target=target, line=line))
    return tuple(links)


# CJK 统一表意文字（含扩展 A 与兼容区）：标签字符集的 CJK 部分
_CJK = "㐀-䶿一-鿿豈-﫿"

#: 标签形态：`#` 前不能是 ASCII 字母数字、`/`（URL 免疫，如 `…com/#frag`）
#: 或另一个 `#`（##tag 排除）；`#` 后紧跟标签字符但首字符不能是 `/`。
#: 标题行（`# `）因空格不在字符集内天然排除。
_TAG_RE = re.compile(r"(?<![A-Za-z0-9#/])#([A-Za-z0-9_\-/" + _CJK + r"]+)")


_LINK_SYNTAX_RE = re.compile(r"\[\[([^\[\]]*)\]\]")


def strip_link_syntax(text: str) -> str:
    """剥离全部 `[[...]]` 链接语法（含别名部分），替换为等长空格保持行结构。

    标签提取前必须过这里：`[[#小节]]` 页内锚与 `[[页面|别名#x]]` 的别名
    部分，其内部 `#` 不得泄漏成标签（spec：`[[#小节]]` 整体跳过、完全不计数）。
    """
    return _LINK_SYNTAX_RE.sub(lambda m: " " * len(m.group(0)), text)


def extract_tags(text: str) -> tuple[str, ...]:
    """从已剥离代码区的正文提取标签（按出现顺序，不去重）。

    纯数字（不含任何字母或 CJK）不是标签：`#1`、`#2024` 豁免。
    """
    tags = []
    for match in _TAG_RE.finditer(text):
        name = match.group(1)
        if not any(ch.isalpha() for ch in name):  # 字母（含 CJK）至少一个
            continue
        tags.append(name)
    return tuple(tags)


def parse_page(text: str, rel_path: str) -> Page:
    """把一个页面的文本解析为 Page 结构。

    frontmatter（若有）单独解析 `title:`/`tags:`；链接与正文标签只从
    正文提取——frontmatter 内的 `[[..]]` 与 `#..` 不产生任何链接或标签。
    """
    body, frontmatter = split_frontmatter(text)
    stripped = strip_code(body)
    title, fm_tags = _parse_frontmatter(frontmatter)
    tags: dict[str, None] = {}  # 去重保序：正文标签在前，frontmatter 并入在后
    for tag in (*extract_tags(strip_link_syntax(stripped)), *fm_tags):
        tags.setdefault(tag)
    return Page(
        path=rel_path,
        name=PurePosixPath(rel_path).stem,
        links=extract_links(stripped),
        title=title,
        tags=tuple(tags),
    )


_FM_DELIM = "---"


def split_frontmatter(text: str) -> tuple[str, str | None]:
    """切分文件头 frontmatter，返回 (正文, frontmatter 块)。

    仅当首行就是 `---` 且存在闭合 `---` 时才视为 frontmatter；
    否则解析失败按无 frontmatter 处理（块为 None，原文整体即正文）。
    """
    lines = text.split("\n")
    if lines[0].strip() != _FM_DELIM:
        return text, None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FM_DELIM:
            return "\n".join(lines[i + 1 :]), "\n".join(lines[1:i])
    return text, None


def _parse_frontmatter(block: str | None) -> tuple[str | None, tuple[str, ...]]:
    """最小解析：只认 `title:` 与 `tags:`（单行列表两种写法），其余行忽略。"""
    if block is None:
        return None, ()
    title: str | None = None
    tags: tuple[str, ...] = ()
    for line in block.split("\n"):
        stripped = line.strip()
        if stripped.startswith("title:"):
            title = _unquote(stripped[len("title:") :].strip())
        elif stripped.startswith("tags:"):
            value = stripped[len("tags:") :].strip()
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]  # 括号列表写法 [a, b]
            tags = tuple(
                item for part in value.split(",") if (item := _unquote(part.strip()))
            )
    return title, tags


def _unquote(value: str) -> str:
    """剥掉一层成对的引号（tags 列表项与 title 值均可带引号）。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value
