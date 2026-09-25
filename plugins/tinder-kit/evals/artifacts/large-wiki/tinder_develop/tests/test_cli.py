"""Seam 5：CLI 薄壳 — 参数解析、渲染与退出码（0 正常 / 1 失败或体检有问题）。"""

import json

import pytest

from wikicore.cli import build_snippet, main
from wikicore.indexer import INDEX_NAME
from wikicore.tokenize import tokenize

HEALTHY = {
    "首页.md": "欢迎 [[指南]] #meta",
    "指南.md": "见 [[首页]] 与 [[断链]] [[孤儿]] #lang/python python 知识库",
    "断链.md": "正常回链 [[指南]]",
    "孤儿.md": "被指南引用",
}


@pytest.fixture
def vault(tmp_path, write_vault):
    write_vault(tmp_path, HEALTHY)
    assert main(["build", "--root", str(tmp_path)]) == 0
    return tmp_path


def test_build_creates_index_and_reports_count(tmp_path, write_vault, capsys):
    write_vault(tmp_path, HEALTHY)

    code = main(["build", "--root", str(tmp_path)])

    assert code == 0
    assert (tmp_path / INDEX_NAME).is_file()
    assert "4" in capsys.readouterr().out


def test_links_and_backlinks_human_and_json(vault, capsys):
    assert main(["links", "指南", "--root", str(vault)]) == 0
    out = capsys.readouterr().out
    for name in ("首页", "断链", "孤儿"):
        assert name in out

    assert main(["backlinks", "首页", "--root", str(vault), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == ["指南"]


def test_tags_aggregate_filter_and_json(vault, capsys):
    assert main(["tags", "--root", str(vault)]) == 0
    out = capsys.readouterr().out
    for tag in ("meta", "lang", "lang/python"):
        assert tag in out

    assert main(["tags", "lang", "--root", str(vault)]) == 0
    assert capsys.readouterr().out.splitlines() == ["指南"]

    assert main(["tags", "--root", str(vault), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"meta": 1, "lang": 1, "lang/python": 1}


def test_search_renders_ranked_result_with_snippet(vault, capsys):
    code = main(["search", "python", "--root", str(vault)])

    assert code == 0
    out = capsys.readouterr().out
    assert "指南" in out
    assert "python" in out  # 摘要可见


def test_build_snippet_keeps_original_case_and_offsets():
    text = "关于 Python 的知识库笔记"

    snippet = build_snippet(text, tokenize("python 知识库"))

    assert "Python" in snippet  # 原文大小写保留（非 casefold 副本）
    assert "知识库" in snippet


def test_build_snippet_windows_long_text_and_falls_back_to_head():
    long_text = "前" * 50 + "关键词needle在中间" + "后" * 50

    snippet = build_snippet(long_text, ["needle"])
    assert snippet.startswith("…") and snippet.endswith("…")
    assert "needle" in snippet

    assert build_snippet("开头几字", ["zzz"]) == "开头几字"


def test_doctor_unhealthy_exit_1_then_healthy_exit_0(tmp_path, write_vault, capsys):
    write_vault(tmp_path, HEALTHY)
    (tmp_path / "断链.md").write_text("断 [[缺失页]]", encoding="utf-8")
    main(["build", "--root", str(tmp_path)])

    code = main(["doctor", "--root", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "死链" in out and "缺失页" in out

    assert main(["doctor", "--root", str(tmp_path), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["healthy"] is False
    assert payload["dead_links"] == [{"page": "断链", "line": 1, "target": "缺失页"}]
    assert payload["orphans"] == []

    (tmp_path / "断链.md").write_text("正常回链 [[指南]]", encoding="utf-8")
    assert main(["build", "--root", str(tmp_path)]) == 0
    assert main(["doctor", "--root", str(tmp_path)]) == 0
    assert "体检通过" in capsys.readouterr().out


def test_doctor_entry_exempt_suppresses_orphan(tmp_path, write_vault, capsys):
    write_vault(tmp_path, {"入口.md": "无人链接的入口页"})
    main(["build", "--root", str(tmp_path)])

    assert main(["doctor", "--root", str(tmp_path)]) == 1
    capsys.readouterr()
    assert main(["doctor", "--entry", "入口", "--root", str(tmp_path)]) == 0
    assert "体检通过" in capsys.readouterr().out


def test_global_options_before_subcommand(vault, capsys):
    assert main(["--root", str(vault), "backlinks", "首页", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == ["指南"]


def test_json_before_subcommand(vault, capsys):
    assert main(["--json", "--root", str(vault), "backlinks", "首页"]) == 0
    assert json.loads(capsys.readouterr().out) == ["指南"]


def test_page_not_found_exit_1(vault, capsys):
    assert main(["backlinks", "不存在的页", "--root", str(vault)]) == 1
    assert "不存在" in capsys.readouterr().err


def test_missing_index_exits_1_hinting_build(tmp_path, write_vault, capsys):
    write_vault(tmp_path, HEALTHY)

    assert main(["backlinks", "首页", "--root", str(tmp_path)]) == 1
    assert "build" in capsys.readouterr().err


def test_duplicate_pagename_build_fails_with_conflict_message(tmp_path, write_vault, capsys):
    write_vault(tmp_path, {"sub1/Notes.md": "一", "sub2/notes.md": "二"})

    assert main(["build", "--root", str(tmp_path)]) == 1
    assert "冲突" in capsys.readouterr().err
    assert not (tmp_path / INDEX_NAME).exists()


def test_stale_index_warns_on_stderr_but_still_answers(vault, capsys):
    (vault / "新页.md").write_text("新内容", encoding="utf-8")

    assert main(["tags", "--root", str(vault)]) == 0
    captured = capsys.readouterr()
    assert "过期" in captured.err
    assert "meta" in captured.out  # 仍按现有索引作答
