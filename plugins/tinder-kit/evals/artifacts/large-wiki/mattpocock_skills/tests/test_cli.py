"""CLI 测试：命令面、输出契约、退出码。"""

from __future__ import annotations

import json

import pytest

from wiki_cli.cli import main


@pytest.fixture
def make_vault(tmp_path):
    def make(files: dict[str, str]):
        for rel, content in files.items():
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return tmp_path

    return make


def run(vault, *argv):
    return main(["--root", str(vault), *argv])


def test_doctor_clean_exits_zero(make_vault, capsys):
    code = run(make_vault({"a.md": "[[b]]", "b.md": "[[a]]"}), "doctor")
    assert code == 0
    assert "未发现缺陷" in capsys.readouterr().out


def test_doctor_defects_exit_one(make_vault, capsys):
    code = run(make_vault({"a.md": "[[缺页]]"}), "doctor")
    assert code == 1
    out = capsys.readouterr().out
    assert "死链" in out and "孤岛页" in out


def test_doctor_json(make_vault, capsys):
    run(make_vault({"a.md": "[[缺页]]"}), "doctor", "--json")
    data = json.loads(capsys.readouterr().out)
    assert data["dead_links"][0]["target"] == "缺页"


def test_backlinks_and_md_suffix_arg(make_vault, capsys):
    root = make_vault({"a.md": "[[目标]]", "目标.md": ""})
    assert run(root, "backlinks", "目标.md") == 0
    assert "a.md:1" in capsys.readouterr().out


def test_backlinks_nonexistent_page_exits_one(make_vault, capsys):
    code = run(make_vault({"a.md": ""}), "backlinks", "不存在")
    assert code == 1
    assert "页面不存在" in capsys.readouterr().err


def test_links_statuses(make_vault, capsys):
    code = run(
        make_vault({"a.md": "[[b]] [[缺页]] [[https://x.com]]", "b.md": ""}),
        "links",
        "a",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "[已解析]" in out and "[死链]" in out and "[外部]" in out


def test_links_ambiguous_status(make_vault, capsys):
    code = run(
        make_vault({"x/dup.md": "", "y/dup.md": "", "a.md": "[[dup]]"}), "links", "a"
    )
    assert code == 0
    assert "[歧义]" in capsys.readouterr().out


def test_links_nonexistent_page_exits_one(make_vault, capsys):
    assert run(make_vault({"a.md": ""}), "links", "不存在") == 1
    assert "页面不存在" in capsys.readouterr().err


def test_tags_summary_and_detail(make_vault, capsys):
    root = make_vault({"a.md": "#py", "b.md": "#py #ml"})
    assert run(root, "tags") == 0
    out = capsys.readouterr().out
    assert "py ×2" in out and "ml ×1" in out
    assert run(root, "tags", "py") == 0
    out = capsys.readouterr().out
    assert "a.md" in out and "b.md" in out


def test_tags_unknown_tag_exits_one(make_vault, capsys):
    assert run(make_vault({"a.md": ""}), "tags", "不存在") == 1
    assert "标签不存在" in capsys.readouterr().err


def test_search_hit_and_miss(make_vault, capsys):
    root = make_vault({"a.md": "谈机器学习"})
    assert run(root, "search", "机器学习") == 0
    assert "a" in capsys.readouterr().out
    assert run(root, "search", "不存在的词") == 1
    assert "无命中" in capsys.readouterr().err


def test_search_json(make_vault, capsys):
    run(make_vault({"python.md": "正文"}), "search", "python", "--json")
    data = json.loads(capsys.readouterr().out)
    assert data["hits"][0]["identity_hit"] is True


def test_build_writes_cache(make_vault, capsys):
    root = make_vault({"a.md": "[[b]]"})
    assert run(root, "build") == 0
    assert (root / ".wiki_index.json").exists()
    assert "1 页" in capsys.readouterr().out


def test_invalid_root_exits_two(tmp_path, capsys):
    assert main(["--root", str(tmp_path / "不存在"), "doctor"]) == 2
    assert "根目录不存在" in capsys.readouterr().err


def test_missing_subcommand_exits_two():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_json_before_subcommand(make_vault, capsys):
    run(make_vault({"a.md": "#t"}), "--json", "tags")
    data = json.loads(capsys.readouterr().out)
    assert data["tags"][0]["tag"] == "t"
