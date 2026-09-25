"""文本解析：frontmatter 切分、wikilink 与正文标签扫描。

本模块固化了全部已拍板的解析语义（严格匹配、不做纠错、代码区排除），
每条规则背后都有一次决策，见 CONTEXT.md 与 docs/adr/。
"""

from __future__ import annotations

import re

from .model import MD_SUFFIX, Page, WikiLink

# [[目标#锚点|别名]]，可带 ! 前缀（嵌入）；内层不允许方括号
WIKILINK_RE = re.compile(r"(!?)\[\[([^\[\]]+)\]\]")

# # 标签。触发条件：前一字符不得是字母/数字/斜杠——排除 C#、URL 锚点
# （x.com/#a）、foo#bar，放行中文括号后与下划线后的标签；标签名不得以数字
# 开头——排除 #1 issue 引用，ATX 标题（# 后跟空格）亦被字符集自动排除；
# `/` 仅是名字里的普通字符，聚合不展开层级。
TAG_RE = re.compile(r"(?<!(?:[^\W_]|/))#([^\W\d][\w\-/]*)")

# 带 scheme:// 的目标是外部链接，排除出链接图；mailto: 无 //，单独识别
URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")

# 围栏代码块（``` 与 ~~~）；闭合围栏须同字符且不短于开栏
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

# 行内代码定界（一个或多个反引号）
INLINE_CODE_RE = re.compile(r"`+")

FRONTMATTER_DELIM = "---"
TAGS_KEY_RE = re.compile(r"^tags:\s*(.*)$")
LIST_ITEM_RE = re.compile(r"^\s+-\s*(.*?)\s*$")


def strip_md(target: str) -> str:
    """匹配的唯一宽容规则：剥离目标末尾的 ``.md`` 后缀（大小写不敏感）。"""
    return target[:-3] if target.lower().endswith(MD_SUFFIX) else target


def read_lines(path) -> list[str]:
    """读取页面为行列表。utf-8-sig 兼容 BOM；编码错误以替换字符降级，不中断体检。"""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def split_frontmatter(lines: list[str]) -> tuple[list[str] | None, list[str], bool]:
    """切分 frontmatter，返回 (元数据行或 None, 正文行, 是否畸形)。

    元数据块必须从第 1 行的 ``---`` 开始并成对闭合；不闭合时不做纠错猜测，
    整体按正文处理，缺陷交给体检暴露。
    """
    if not lines or lines[0].strip() != FRONTMATTER_DELIM:
        return None, lines, False
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_DELIM:
            return lines[1:i], lines[i + 1 :], False
    return None, lines, True


def frontmatter_tags(fm_lines: list[str]) -> list[str]:
    """从 frontmatter 提取 ``tags:`` 键（唯一被识别的键），行内与逐行两种形式。

    自写行级迷你解析，不引入 PyYAML；畸形行（如未闭合的行内列表）静默跳过，
    交给体检暴露。
    """
    for i, line in enumerate(fm_lines):
        m = TAGS_KEY_RE.match(line)
        if not m:
            continue
        rest = m.group(1).strip()
        tags: list[str] = []
        if rest.startswith("["):
            if rest.endswith("]"):
                tags = [t.strip() for t in rest[1:-1].split(",") if t.strip()]
            # 未闭合的行内列表视为畸形，跳过
        elif rest:
            tags = [rest]
        else:
            for cont in fm_lines[i + 1 :]:
                item = LIST_ITEM_RE.match(cont)
                if not item:
                    break
                if item.group(1):
                    tags.append(item.group(1))
        return tags
    return []


def _outside_inline_code(line: str) -> str:
    """剔除行内代码段后返回可扫描文本。

    反引号成对闭合时，偶数下标段为代码外文本；不闭合时只保留首段（保守）。
    """
    parts = INLINE_CODE_RE.split(line) if "`" in line else [line]
    if len(parts) % 2 == 1:
        return "".join(parts[0::2])
    return parts[0]


def _parse_inner(
    inner: str, line_no: int, links: list[WikiLink], embed: bool = False
) -> None:
    head, _, alias = inner.partition("|")
    target_part, _, anchor = head.partition("#")
    raw_target = target_part.strip()
    if not raw_target:
        return  # [[]] 或 [[#小节]] 形式：无页面目标，v1 不处理
    alias = alias.strip() or None
    anchor = anchor.strip() or None
    if URI_RE.match(raw_target) or raw_target.lower().startswith("mailto:"):
        links.append(
            WikiLink(
                target=raw_target,
                raw=raw_target,
                line=line_no,
                alias=alias,
                anchor=anchor,
                embed=embed,
                external=True,
            )
        )
        return
    links.append(
        WikiLink(
            target=strip_md(raw_target),
            raw=raw_target,
            line=line_no,
            alias=alias,
            anchor=anchor,
            embed=embed,
        )
    )


def _scan_line(text: str, line_no: int, links: list[WikiLink], tags: list[str]) -> None:
    for m in WIKILINK_RE.finditer(text):
        _parse_inner(m.group(2), line_no, links, embed=m.group(1) == "!")
    for m in TAG_RE.finditer(text):
        tag = m.group(1)
        if tag.endswith("/") or "//" in tag:
            continue  # 空层级的嵌套形式不构成合法标签
        tags.append(tag)


def scan_body(
    body_lines: list[str], line_offset: int
) -> tuple[list[WikiLink], list[str]]:
    """扫描正文，返回 (链接, 标签)。行号以整个文件计（含 frontmatter 偏移）。

    围栏代码块与行内代码内的 wikilink 和 #tag 一律不算——代码里的注释、
    include、示例不参与链接图与标签聚合。
    """
    links: list[WikiLink] = []
    tags: list[str] = []
    fence: tuple[str, int] | None = None
    for i, line in enumerate(body_lines):
        m = FENCE_RE.match(line)
        if m:
            marker = m.group(1)
            ch, length = marker[0], len(marker)
            if fence is None:
                fence = (ch, length)
                continue  # 开栏行（含信息串）不扫描
            if ch == fence[0] and length >= fence[1]:
                fence = None
                continue
        if fence is not None:
            continue
        _scan_line(_outside_inline_code(line), line_offset + i + 1, links, tags)
    return links, tags


def parse_page(
    name: str, rel_path: str, size: int, mtime_ns: int, lines: list[str]
) -> Page:
    """把一个文件的行解析为 Page。"""
    fm, body, malformed = split_frontmatter(lines)
    links, body_tags = scan_body(body, len(lines) - len(body))
    fm_tags = frontmatter_tags(fm) if fm else []
    tags = sorted(set(fm_tags + body_tags))
    return Page(
        name=name,
        rel_path=rel_path,
        size=size,
        mtime_ns=mtime_ns,
        tags=tuple(tags),
        links=tuple(links),
        malformed_frontmatter=malformed,
    )
