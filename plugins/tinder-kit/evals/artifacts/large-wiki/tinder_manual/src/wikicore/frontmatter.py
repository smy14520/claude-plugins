"""极简 frontmatter 识别与 `tags:` 键解析（不引入 PyYAML，见 ADR-0002）。"""

from __future__ import annotations


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """返回 (frontmatter 行列表, 正文)；首行非 `---` 或未闭合时视为无 frontmatter。"""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    return [], text


def parse_frontmatter_tags(fm_lines: list[str]) -> list[str]:
    """仅识别 `tags:` 键：行内数组 / 逗号分隔 / 多行 `- ` 列表三种写法（Q13）。"""
    tags: list[str] = []
    in_list = False
    for line in fm_lines:
        stripped = line.strip()
        if not in_list:
            if stripped.startswith("tags:"):
                value = stripped[len("tags:") :].strip()
                if value:
                    tags.extend(_split_inline(value))
                else:
                    in_list = True  # 进入多行列表模式
            continue
        if not stripped:
            continue
        if stripped.startswith("- "):
            tags.append(_clean(stripped[2:]))
        else:
            in_list = False  # 列表结束
    return tags


def _split_inline(value: str) -> list[str]:
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    if not v:
        return []
    return [_clean(item) for item in v.split(",")]


def _clean(item: str) -> str:
    item = item.strip().strip("'\"").strip()
    if item.startswith("#"):
        item = item[1:].strip()
    return item
