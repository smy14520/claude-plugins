"""End-to-end CLI tests, including Chinese filenames and case handling."""
import json

import pytest

from wikicli.cli import main


@pytest.fixture
def vault_root(make_vault):
    return make_vault(
        {
            "notes/python.md": "# Python 笔记\n#lang/python\n相关: [[中文页面]]\n",
            "中文页面.md": "# 中文\n被 [[python]] 引用，含 知识图谱 关键词\n#lang/python\n",
            "lonely.md": "nobody links here [[ghost]]\n",
            "a/dup.md": "",
            "b/dup.md": "",
        }
    )


def run(root, *argv):
    return main(["--vault", str(root), *argv])


class TestLinksBacklinks:
    def test_links_text_and_json(self, vault_root, capsys):
        assert run(vault_root, "links", "python") == 0
        out = capsys.readouterr().out
        assert "notes/python.md" in out
        assert "[[中文页面]]" in out

        assert run(vault_root, "links", "PYTHON", "--json") == 0
        data = json.loads(capsys.readouterr().out)
        assert data["page"] == "notes/python.md"
        assert data["links"][0]["resolved"] == "中文页面.md"

    def test_backlinks(self, vault_root, capsys):
        assert run(vault_root, "backlinks", "中文页面", "--json") == 0
        data = json.loads(capsys.readouterr().out)
        assert data["backlinks"][0]["source"] == "notes/python.md"

    def test_unknown_page_exit_2(self, vault_root, capsys):
        assert run(vault_root, "links", "missing") == 2
        assert "no page named" in capsys.readouterr().err

    def test_ambiguous_page_arg_exit_2(self, vault_root, capsys):
        assert run(vault_root, "backlinks", "dup") == 2
        assert "ambiguous" in capsys.readouterr().err


class TestTags:
    def test_aggregate(self, vault_root, capsys):
        assert run(vault_root, "tags", "--json") == 0
        data = json.loads(capsys.readouterr().out)
        tags = {t["tag"]: t["count"] for t in data["tags"]}
        assert tags == {"lang/python": 2}

    def test_tag_pages_includes_descendants(self, vault_root, capsys):
        assert run(vault_root, "tags", "lang/python") == 0
        out = capsys.readouterr().out
        assert "中文页面.md" in out
        assert "notes/python.md" in out


class TestSearch:
    def test_chinese_keyword(self, vault_root, capsys):
        assert run(vault_root, "search", "知识图谱") == 0
        assert "中文页面.md" in capsys.readouterr().out

    def test_multi_keyword_and_json(self, vault_root, capsys):
        assert run(vault_root, "search", "笔记", "python", "--json") == 0
        data = json.loads(capsys.readouterr().out)
        assert data["results"][0]["page"] == "notes/python.md"

    def test_no_results_exit_0(self, vault_root, capsys):
        assert run(vault_root, "search", "zzzz") == 0
        assert "No pages match" in capsys.readouterr().out


class TestDoctor:
    def test_findings_exit_1(self, vault_root, capsys):
        assert run(vault_root, "doctor") == 1
        out = capsys.readouterr().out
        assert "Dead links (1)" in out
        assert "Orphan pages (3)" in out

    def test_json_counts(self, vault_root, capsys):
        assert run(vault_root, "doctor", "--json") == 1
        data = json.loads(capsys.readouterr().out)
        assert len(data["dead_links"]) == 1
        assert len(data["orphan_pages"]) == 3

    def test_clean_vault_exit_0(self, make_vault, capsys):
        root = make_vault({"a.md": "[[b]]", "b.md": "[[a]]"})
        assert run(root, "doctor") == 0
        assert "healthy" in capsys.readouterr().out


class TestVaultFlag:
    def test_vault_after_subcommand(self, vault_root, capsys):
        assert main(["tags", "--vault", str(vault_root)]) == 0
        assert capsys.readouterr().out

    def test_missing_vault_exit_2(self, capsys):
        assert main(["--vault", "/nonexistent/zzz", "doctor"]) == 2
        assert "not found" in capsys.readouterr().err
