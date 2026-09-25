"""CLI 端到端：退出码、--json 结构、落盘索引（Q8/Q14/Q15/Q16）。"""

import json

from wikicore.cli import main


def test_build_writes_index_and_summary(vault, capsys):
    root = vault({"a.md": "#t [[b]]", "b.md": "回链 [[a]] #t"})
    assert main(["--root", str(root), "build"]) == 0
    data = json.loads((root / ".wiki_index.json").read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert "索引已写入" in capsys.readouterr().out


def test_build_json(vault, capsys):
    root = vault({"a.md": "x"})
    assert main(["--root", str(root), "build", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["pages"] == 1


def test_backlinks_human_and_json(vault, capsys):
    root = vault({"a.md": "[[b]]", "b.md": "内容", "c.md": "[[b]]"})
    assert main(["--root", str(root), "backlinks", "b"]) == 0
    assert "a" in capsys.readouterr().out
    assert main(["--root", str(root), "backlinks", "b", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert sorted(s["title"] for s in payload["sources"]) == ["a", "c"]


def test_backlinks_unknown_page_exits_1(vault, capsys):
    root = vault({"a.md": "x"})
    assert main(["--root", str(root), "backlinks", "ghost"]) == 1


def test_links_marks_dead_targets(vault, capsys):
    root = vault({"a.md": "[[b]] [[ghost]]", "b.md": "x"})
    assert main(["--root", str(root), "links", "a"]) == 0
    out = capsys.readouterr().out
    assert "死链" in out and "ghost" in out


def test_tags_aggregation_and_filter(vault, capsys):
    root = vault({"a.md": "#python", "b.md": "#python #java", "c.md": "#java"})
    assert main(["--root", str(root), "tags"]) == 0
    out = capsys.readouterr().out
    assert "#python（2 页）" in out and "#java（2 页）" in out
    assert main(["--root", str(root), "tags", "#python", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tag"] == "python" and len(payload["pages"]) == 2


def test_search_json_sorted_by_count(vault, capsys):
    root = vault({"a.md": "hello world", "b.md": "说 hello"})
    assert main(["--root", str(root), "search", "hello", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [h["title"] for h in payload["hits"]] == ["a", "b"]


def test_doctor_exit_code_semantics(vault):
    dirty = vault(
        {
            "home.md": "[[other]]",
            "other.md": "x",
            "lone.md": "y",
            "bad.md": "[[ghost]]",
        }
    )
    assert main(["--root", str(dirty), "doctor"]) == 1  # 死链 → 1

    warn_only = vault({"home.md": "[[other]]", "other.md": "x", "lone.md": "y"})
    assert main(["--root", str(warn_only), "doctor"]) == 0  # 孤岛仅警告
    assert main(["--root", str(warn_only), "doctor", "--strict"]) == 1
    assert (
        main(
            [
                "--root",
                str(warn_only),
                "doctor",
                "--ignore",
                "lone",
                "--ignore",
                "home",
                "--strict",
            ]
        )
        == 0  # 全部孤岛被豁免后，strict 亦通过
    )


def test_doctor_json_payload(vault, capsys):
    root = vault({"a.md": "[[ghost]] [[b]]", "b.md": "x"})
    assert main(["--root", str(root), "doctor", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["dead_links"] == [{"source": "a", "target": "ghost"}]
    assert payload["orphans"] == ["a"]  # a 只有出链，零入链


def test_missing_root_exits_2(capsys):
    assert main(["--root", "/nonexistent/xyz/wiki", "build"]) == 2
