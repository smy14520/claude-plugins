"""Seam 2：索引构建与持久化的公共行为。"""

import os

import pytest

from wikicore.indexer import (
    INDEX_NAME,
    DuplicatePageError,
    IndexNotFound,
    build_index,
    index_out_of_date,
    load_index,
    save_index,
)


def test_build_collects_pages_links_tags_and_bigram_postings(tmp_path, write_vault):
    write_vault(tmp_path, {
        "首页.md": "欢迎 [[页面B]] #lang/python\n另见 [[页面C]]",
        "子目录/页面B.md": "这是知识库 #知识 #lang",
        "页面C.md": "更多内容",
        ".hidden/忽略.md": "[[谁]]",
    })

    index = build_index(tmp_path)

    assert set(index.pages) == {"首页", "页面B", "页面C"}
    assert index.pages["首页"].file == "首页.md"
    assert [link.target for link in index.pages["首页"].links] == ["页面B", "页面C"]
    assert index.pages["首页"].tags == ["lang/python"]
    assert index.pages["页面B"].tags == ["知识", "lang"]
    # ADR-0003：CJK 二元组进倒排（"知识库" → "知识"/"识库"）
    assert index.postings["识库"] == {"页面B": 1}
    assert index.postings["lang"] == {"首页": 1, "页面B": 1}


def test_duplicate_pagename_case_insensitive(tmp_path, write_vault):
    write_vault(tmp_path, {"sub1/Notes.md": "一", "sub2/notes.md": "二"})

    with pytest.raises(DuplicatePageError):
        build_index(tmp_path)

    assert not (tmp_path / INDEX_NAME).exists()


def test_save_load_roundtrip_is_lossless_and_atomic(tmp_path, write_vault):
    write_vault(tmp_path, {"a.md": "[[b]] #t", "b.md": "回链 [[A]]"})
    index = build_index(tmp_path)

    save_index(index, tmp_path)

    assert (tmp_path / INDEX_NAME).exists()
    assert not (tmp_path / (INDEX_NAME + ".tmp")).exists()
    assert load_index(tmp_path) == index


def test_load_missing_index_raises(tmp_path):
    with pytest.raises(IndexNotFound):
        load_index(tmp_path)


def test_incremental_rebuild_equals_full_rebuild(tmp_path, write_vault):
    write_vault(tmp_path, {"a.md": "[[b]]", "b.md": "内容一", "c.md": "待删除"})
    first = build_index(tmp_path)

    write_vault(tmp_path, {"b.md": "内容二已修改", "d.md": "新页面"})
    (tmp_path / "c.md").unlink()

    incremental = build_index(tmp_path, previous=first)
    fresh = build_index(tmp_path)

    assert incremental == fresh


def test_index_out_of_date_detection(tmp_path, write_vault):
    write_vault(tmp_path, {"a.md": "一"})
    index = build_index(tmp_path)
    assert index_out_of_date(index, tmp_path) is False

    path = tmp_path / "a.md"
    os.utime(path, (path.stat().st_mtime + 10,) * 2)
    assert index_out_of_date(index, tmp_path) is True

    write_vault(tmp_path, {"新增.md": "二"})
    index = build_index(tmp_path)
    assert index_out_of_date(index, tmp_path) is False
    write_vault(tmp_path, {"another.md": "三"})
    assert index_out_of_date(index, tmp_path) is True
