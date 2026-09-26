"""CLI seam（主 seam）端到端：临时 Vault → wiki links → stdout / 退出码 / JSON 结构。

LinkGraph / 页面名注册表 / 中文输出 / 健壮性均在此层以外部可见行为验收。
"""

import contextlib
import io
import json
import os
import tempfile
import unicodedata
import unittest
from pathlib import Path

from wiki_cli.cli import main


class VaultFixtureTest(unittest.TestCase):
    """以临时目录构造 Vault，Vault 目录按约定写在子命令之前。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name)

    def write_page(self, rel: str, text: str) -> None:
        path = self.vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_wiki(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([str(self.vault), *argv])
        return code, out.getvalue(), err.getvalue()


class LinksOfPageTest(VaultFixtureTest):

    def test_lists_all_links_with_target_and_file_line(self):
        self.write_page("foo.md", "# Foo\n见 [[Bar]] 与 [[中文页面]]。\n再 [[Bar]] 一次。\n")
        self.write_page("bar.md", "Bar 正文")
        self.write_page("中文页面.md", "中文正文")
        code, out, _ = self.run_wiki("links", "Foo")
        self.assertEqual(code, 0)
        # 行格式 = 来源 `文件:行号` → 目标页面名
        self.assertIn("foo.md:2 → bar", out)
        self.assertIn("foo.md:2 → 中文页面", out)
        self.assertIn("foo.md:3 → bar", out)
        self.assertIn("3 个 Link", out)

    def test_duplicate_targets_are_listed_per_occurrence(self):
        self.write_page("a.md", "[[B]] [[B]]")
        self.write_page("b.md", "x")
        code, out, _ = self.run_wiki("links", "a", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["link_count"], 2)

    def test_alias_and_anchor_links_resolve_to_page(self):
        self.write_page("a.md", "[[Real|别名]] 与 [[Real#小节]]")
        self.write_page("real.md", "x")
        code, out, _ = self.run_wiki("links", "a", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["link_count"], 2)
        self.assertEqual(
            [link["resolved_page"] for link in data["links"]], ["real", "real"]
        )

    def test_unresolved_target_listed_with_raw_text(self):
        self.write_page("a.md", "指向 [[Ghost]]")
        code, out, _ = self.run_wiki("links", "a")
        self.assertEqual(code, 0)
        self.assertIn("Ghost", out)

    def test_page_not_found_is_usage_error_exit_2(self):
        self.write_page("a.md", "x")
        code, _, err = self.run_wiki("links", "不存在的页面")
        self.assertEqual(code, 2)
        self.assertIn("页面不存在", err)
        self.assertIn("不存在的页面", err)


class LinksSummaryTest(VaultFixtureTest):

    def test_summary_lists_every_page_with_links_and_totals(self):
        self.write_page("foo.md", "[[Bar]] 与 [[Baz]]")
        self.write_page("bar.md", "回到 [[Foo]]")
        self.write_page("baz.md", "无出链")
        code, out, _ = self.run_wiki("links")
        self.assertEqual(code, 0)
        self.assertIn("3 个 Page", out)
        self.assertIn("3 个 Link", out)
        self.assertIn("foo.md:1", out)
        self.assertIn("bar.md:1", out)
        # 无出链的 Page 不占汇总条目（孤岛可见性归 doctor）
        self.assertNotIn("baz.md", out)

    def test_summary_over_empty_vault_is_graceful_exit_0(self):
        code, out, _ = self.run_wiki("links")
        self.assertEqual(code, 0)
        self.assertIn("没有 Page", out)

    def test_summary_when_no_page_has_links_is_graceful_exit_0(self):
        self.write_page("lonely.md", "只有文字")
        code, out, _ = self.run_wiki("links")
        self.assertEqual(code, 0)
        self.assertIn("均无 Link", out)


class PageNameRegistryTest(VaultFixtureTest):
    """页面身份：casefold 大小写不敏感 + Unicode NFC 归一。"""

    def test_casefold_link_hits_page_written_in_other_case(self):
        self.write_page("foo.md", "内容")
        self.write_page("a.md", "[[FOO]]")
        self.write_page("b.md", "[[foo]]")
        code, out, _ = self.run_wiki("links", "a", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["links"][0]["resolved_page"], "foo")
        code, out, _ = self.run_wiki("links", "b", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["links"][0]["resolved_page"], "foo")

    def test_page_argument_is_case_insensitive_too(self):
        self.write_page("mixed.md", "见 [[Target]]")
        self.write_page("target.md", "x")
        code, out, _ = self.run_wiki("links", "MIXED")
        self.assertEqual(code, 0)
        self.assertIn("页面 mixed 的 1 个 Link", out)
        self.assertIn("mixed.md:1 → target", out)

    def test_nfc_link_resolves_nfd_filename(self):
        nfd_name = unicodedata.normalize("NFD", "café")
        self.write_page(nfd_name + ".md", "NFD 文件名")
        self.write_page("src.md", "[[café]]")  # NFC 形态的链接目标
        code, out, _ = self.run_wiki("links", "src", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["links"][0]["resolved_page"], "café")

    def test_nfd_link_resolves_nfc_filename(self):
        self.write_page("café.md", "NFC 文件名")
        nfd_target = unicodedata.normalize("NFD", "café")
        self.write_page("src.md", f"[[{nfd_target}]]")
        code, out, _ = self.run_wiki("links", "src", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["links"][0]["resolved_page"], "café")

    def test_mixed_chinese_english_page_name_resolves_case_insensitively(self):
        self.write_page("混合Mixed.md", "中英混合页面")
        self.write_page("a.md", "见 [[混合MIXED]]")
        code, out, _ = self.run_wiki("links", "a")
        self.assertEqual(code, 0)
        self.assertIn("a.md:1 → 混合Mixed", out)


class SubdirDiscoveryTest(VaultFixtureTest):

    def test_subdir_pages_discovered_and_exact_path_link_resolves(self):
        self.write_page("目录/内页.md", "子目录页面")
        self.write_page("sub/inner.md", "nested page")
        self.write_page("root.md", "[[目录/内页]] 与 [[sub/inner]]")
        code, out, _ = self.run_wiki("links", "root")
        self.assertEqual(code, 0)
        self.assertIn("root.md:1 → 目录/内页", out)
        self.assertIn("root.md:1 → sub/inner", out)

    def test_basename_link_finds_subdir_page_globally(self):
        self.write_page("sub/inner.md", "nested page")
        self.write_page("root.md", "[[inner]]")
        code, out, _ = self.run_wiki("links", "root", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["links"][0]["resolved_page"], "sub/inner")


class CodeExclusionEndToEndTest(VaultFixtureTest):

    def test_links_inside_code_blocks_are_not_outgoing_links(self):
        self.write_page(
            "a.md",
            "[[Real]]\n```\n[[Ghost]]\n```\n示例 `[[Ghost2]]` 与 [[Also Real]]\n",
        )
        self.write_page("real.md", "x")
        self.write_page("also_real.md", "x")
        code, out, _ = self.run_wiki("links", "a", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["link_count"], 2)
        self.assertEqual(
            [(link["target"], link["line"]) for link in data["links"]],
            [("Real", 1), ("Also Real", 5)],
        )
        self.assertNotIn("Ghost", out)


class LinksJsonContractTest(VaultFixtureTest):
    """--json 稳定英文字段结构。"""

    def test_single_page_json_structure(self):
        self.write_page("foo.md", "见 [[Bar]] 与 [[Ghost]]")
        self.write_page("bar.md", "x")
        code, out, _ = self.run_wiki("links", "foo", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(
            set(data),
            {"command", "vault", "page", "file", "link_count", "links"},
        )
        self.assertEqual(data["command"], "links")
        self.assertEqual(data["page"], "foo")
        self.assertEqual(data["file"], "foo.md")
        self.assertEqual(data["link_count"], 2)
        self.assertEqual(
            [set(link) for link in data["links"]],
            [{"file", "line", "target", "resolved_page"}] * 2,
        )
        self.assertEqual(data["links"][0]["resolved_page"], "bar")
        self.assertIsNone(data["links"][1]["resolved_page"])
        self.assertEqual(data["links"][0]["line"], 1)

    def test_summary_json_structure(self):
        self.write_page("foo.md", "[[Bar]]")
        self.write_page("bar.md", "x")
        code, out, _ = self.run_wiki("links", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(
            set(data), {"command", "vault", "page_count", "link_count", "pages"}
        )
        self.assertEqual(data["page_count"], 2)
        self.assertEqual(data["link_count"], 1)
        self.assertEqual(len(data["pages"]), 1)
        page_entry = data["pages"][0]
        self.assertEqual(
            set(page_entry), {"page", "file", "link_count", "links"}
        )
        self.assertEqual(page_entry["page"], "foo")

    def test_json_flag_accepted_before_and_after_subcommand(self):
        self.write_page("foo.md", "[[Bar]]")
        self.write_page("bar.md", "x")
        for argv in (("--json", "links", "foo"), ("links", "foo", "--json")):
            with self.subTest(argv=argv):
                code, out, _ = self.run_wiki(*argv)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out)["command"], "links")


class DefaultVaultTest(unittest.TestCase):
    """省略 Vault 目录时默认当前目录。"""

    def test_links_defaults_to_current_directory(self):
        with tempfile.TemporaryDirectory() as empty:
            previous = os.getcwd()
            os.chdir(empty)
            try:
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main(["links"])
            finally:
                os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertIn("没有 Page", out.getvalue())


if __name__ == "__main__":
    unittest.main()
