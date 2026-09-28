"""Doctor findings: dead links, ambiguous links, orphan pages."""


class TestDoctor:
    def test_findings(self, vault_of):
        vault = vault_of(
            {
                "notes/a.md": "[[ghost]] and [[dup]]",
                "x/dup.md": "lonely",
                "y/dup.md": "",
            }
        )
        report = vault.doctor()
        assert [r.link.raw for r in report.dead] == ["ghost"]
        assert len(report.ambiguous) == 1
        # Ambiguous links resolve to nobody, so every page here is orphaned.
        assert [p.path.as_posix() for p in report.orphans] == [
            "notes/a.md",
            "x/dup.md",
            "y/dup.md",
        ]

    def test_clean_vault(self, vault_of):
        vault = vault_of({"a.md": "#t\nsee [[b]]", "b.md": "back [[a]]"})
        assert not vault.doctor().has_findings

    def test_self_link_prevents_orphan(self, vault_of):
        assert vault_of({"s.md": "[[S]]"}).doctor().orphans == ()

    def test_dead_link_location_is_reported(self, vault_of):
        vault = vault_of({"a.md": "one\ntwo\n[[ghost]]"})
        (finding,) = vault.doctor().dead
        assert finding.link.line == 3
        assert finding.link.page.path.as_posix() == "a.md"
