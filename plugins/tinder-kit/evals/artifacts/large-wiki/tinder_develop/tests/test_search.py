"""Full-text search semantics: AND, ranking, casefolding, snippets."""


class TestSearch:
    def test_and_semantics(self, vault_of):
        vault = vault_of(
            {
                "both.md": "has 知识 and 图谱",
                "only-one.md": "has 知识 only",
            }
        )
        results = vault.search(["知识", "图谱"])
        assert [r.page.name for r in results] == ["both"]

    def test_title_beats_content(self, vault_of):
        vault = vault_of(
            {
                "content-heavy.md": "kw\n" * 5,
                "titled.md": "# kw title\nplain body",
            }
        )
        results = vault.search(["kw"])
        assert results[0].page.name == "titled"
        assert results[0].title_hits == 1

    def test_case_insensitive_english(self, vault_of):
        vault = vault_of({"p.md": "Upper PYTHON body"})
        assert vault.search(["python"])[0].page.name == "p"

    def test_chinese_substring(self, vault_of):
        vault = vault_of({"p.md": "这是一个关于知识图谱的笔记"})
        assert vault.search(["知识图谱"])[0].page.name == "p"

    def test_snippet_lines_absolute_and_capped(self, vault_of):
        body = "---\ntags: x\n---\nline1\nkw here\nagain kw\nmore kw\n"
        result = vault_of({"p.md": body}).search(["kw"])[0]
        assert [h.line for h in result.hits] == [5, 6, 7]  # body starts at file line 4
        assert "kw" in result.hits[0].snippet

    def test_no_results(self, vault_of):
        assert vault_of({"p.md": "nothing"}).search(["zzz"]) == []

    def test_code_block_content_is_searchable(self, vault_of):
        vault = vault_of({"p.md": "```\nkw in code\n```"})
        assert len(vault.search(["kw"])) == 1
