"""Seam 3 & 4：Index 查询面（backlinks / tags）与体检（doctor）的公共行为。

大小写不敏感指同名 casefold 匹配（`GUIDE.md` ↔ `[[guide]]`），
绝非跨语言名映射 — `[[缺失页]]` 这类指向不存在页面的链接是死链。
"""

import pytest

from wikicore.health import check
from wikicore.indexer import build_index

FILES = {
    "首页.md": "欢迎 [[指南]] #meta",
    "指南.md": "见 [[深度]] 与 [[首页]] #lang/python",
    "深度.md": "回 [[指南]] #lang/python",
    "叶子.md": "只出不进 [[指南]] #lang",
    "GUIDE.md": "英文页面，被小写链接命中",
    "断链.md": "指向 [[缺失页]] 与 [[guide]]",
    "孤儿.md": "无人链接我",
}


@pytest.fixture
def index(tmp_path, write_vault):
    write_vault(tmp_path, FILES)
    return build_index(tmp_path)


def test_backlinks_case_insensitive_and_sorted(index):
    assert index.backlinks("指南") == sorted(["首页", "深度", "叶子"])
    assert index.backlinks("guide") == index.backlinks("GUIDE") == ["断链"]
    assert index.backlinks("不存在的页") == []


def test_resolve_normalizes_pagename(index):
    assert index.resolve("  指南 ") == "指南"
    assert index.resolve("guide") == "GUIDE"
    assert index.resolve("缺失页") is None


def test_tag_counts_include_ancestor_prefixes(index):
    assert index.tag_counts() == {"meta": 1, "lang": 3, "lang/python": 2}


def test_pages_under_tag_includes_descendants(index):
    assert index.pages_under_tag("lang") == sorted(["指南", "深度", "叶子"])
    assert index.pages_under_tag("lang/python") == sorted(["指南", "深度"])
    assert index.pages_under_tag("meta") == ["首页"]
    assert index.pages_under_tag("不存在") == []


def test_doctor_finds_dead_links_and_orphans(index):
    report = check(index)

    assert [(d.page, d.line, d.target) for d in report.dead_links] == [
        ("断链", 1, "缺失页")
    ]
    # 断链/叶子只出不进，同属孤岛（Q8-A：悬空叶子也算）
    assert report.orphans == sorted(["叶子", "孤儿", "断链"])


def test_doctor_entry_exempt_removes_orphan_flag(index):
    report = check(index, entries=["叶子", "断链", "不存在的入口"])

    assert report.orphans == ["孤儿"]
    assert len(report.dead_links) == 1
