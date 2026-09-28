"""Link resolution through the Vault index: statuses, backlinks."""
from wikicli.model import AMBIGUOUS, DEAD, OK


def by_raw_line(vault, page):
    return {(r.link.raw, r.link.line): r for r in vault.resolved_links_of(page)}


class TestResolution:
    def test_ok_by_stem_case_insensitive(self, vault_of):
        vault = vault_of({"foo.md": "", "bar.md": ""})
        status, target, candidates = vault.resolve("FOO")
        assert status == OK
        assert target.name == "foo"
        assert candidates == ()

    def test_md_suffix_accepted(self, vault_of):
        assert vault_of({"foo.md": ""}).resolve("foo.md")[0] == OK

    def test_dead(self, vault_of):
        assert vault_of({}).resolve("nope")[0] == DEAD

    def test_ambiguous_bare_stem(self, vault_of):
        vault = vault_of({"a/dup.md": "", "b/dup.md": ""})
        status, _, candidates = vault.resolve("dup")
        assert status == AMBIGUOUS
        assert len(candidates) == 2

    def test_subpath_disambiguates(self, vault_of):
        vault = vault_of({"a/dup.md": "", "b/dup.md": ""})
        status, page, _ = vault.resolve("b/dup")
        assert status == OK
        assert page.path.as_posix() == "b/dup.md"

    def test_unique_stem_in_subdir_resolves_bare(self, vault_of):
        assert vault_of({"notes/only.md": ""}).resolve("only")[0] == OK


class TestResolvedLinks:
    def test_statuses_and_lines(self, vault_of):
        vault = vault_of(
            {
                "a.md": "x\n[[b]] mid\n[[ghost]]\n[[dup]]",
                "b.md": "",
                "d1/dup.md": "",
                "d2/dup.md": "",
            }
        )
        page = vault.pages[0]
        resolved = by_raw_line(vault, page)
        assert resolved[("b", 2)].status == OK
        assert resolved[("ghost", 3)].status == DEAD
        assert resolved[("dup", 4)].status == AMBIGUOUS
        assert len(resolved[("dup", 4)].candidates) == 2

    def test_frontmatter_links_do_not_count(self, vault_of):
        vault = vault_of({"a.md": "---\nrelated: [[b]]\n---\nbody", "b.md": ""})
        assert vault.links_of(vault.pages[0]) == []

    def test_links_survive_thematic_break_opening(self, vault_of):
        # a page opening with a --- rule is body, not frontmatter
        vault = vault_of({"a.md": "---\nintro\n---\nsee [[b]]", "b.md": ""})
        assert [link.target for link in vault.links_of(vault.pages[0])] == ["b"]

    def test_no_false_dead_from_embed_or_anchor(self, vault_of):
        vault = vault_of({"a.md": "![[img.png]] [[b#sec]] [[A]]", "b.md": ""})
        assert not vault.doctor().has_findings


class TestBacklinks:
    def test_sources_and_lines(self, vault_of):
        vault = vault_of(
            {
                "target.md": "",
                "x.md": "ref [[target]]",
                "y.md": "line1\nline2 [[TARGET]] again",
            }
        )
        page = next(p for p in vault.pages if p.name == "target")
        back = vault.backlinks_of(page)
        assert {(link.page.name, link.line) for link in back} == {("x", 1), ("y", 2)}

    def test_self_link_counts(self, vault_of):
        vault = vault_of({"solo.md": "note to [[Solo]]"})
        assert [link.page.name for link in vault.backlinks_of(vault.pages[0])] == ["solo"]

    def test_dead_links_grant_no_backlink(self, vault_of):
        vault = vault_of({"a.md": "[[nowhere]]", "b.md": ""})
        assert vault.backlinks_of(vault.pages[1]) == []
