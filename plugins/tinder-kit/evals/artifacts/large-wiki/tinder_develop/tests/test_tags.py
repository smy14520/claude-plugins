"""Tag extraction and aggregation through the Vault index."""


class TestTagsOf:
    def test_body_frontmatter_and_code_boundaries(self, vault_of):
        vault = vault_of(
            {
                "p.md": (
                    "---\ntags: [fm-tag, shared]\n---\n"
                    "# Heading\n#real inline\n"
                    "```bash\n#fenced [[x]]\n```\n"
                    "again #shared and `#inline-only`\n"
                )
            }
        )
        tags = {hit.tag for hit in vault.tags_of(vault.pages[0])}
        assert tags == {"fm-tag", "shared", "real"}

    def test_frontmatter_tag_has_no_line(self, vault_of):
        vault = vault_of({"p.md": "---\ntags: a\n---\nbody"})
        hits = vault.tags_of(vault.pages[0])
        fm_hit = next(h for h in hits if h.tag == "a")
        assert fm_hit.line is None


class TestTagIndex:
    def test_distinct_per_page_counts(self, vault_of):
        vault = vault_of({"a.md": "#x #x #y", "b.md": "#x"})
        entries = {e.key: e for e in vault.tag_index()}
        assert len(entries["x"].pages) == 2
        assert len(entries["y"].pages) == 1

    def test_casefold_grouping_display_first_seen(self, vault_of):
        vault = vault_of({"a.md": "#Python", "b.md": "#python"})
        entries = vault.tag_index()
        assert len(entries) == 1
        assert entries[0].tag == "Python"  # first occurrence in page order
        assert len(entries[0].pages) == 2

    def test_chinese_tag(self, vault_of):
        vault = vault_of({"a.md": "#工作"})
        assert [e.key for e in vault.tag_index()] == ["工作"]

    def test_nested_sorted_under_parent(self, vault_of):
        vault = vault_of({"a.md": "#proj/alpha #proj #other"})
        assert [e.key for e in vault.tag_index()] == ["other", "proj", "proj/alpha"]

    def test_query_includes_descendants(self, vault_of):
        vault = vault_of(
            {
                "a.md": "#proj",
                "b.md": "#proj/alpha",
                "c.md": "#other",
            }
        )
        matched = [e for e in vault.tag_index() if e.key == "proj" or e.key.startswith("proj/")]
        assert {e.key for e in matched} == {"proj", "proj/alpha"}
