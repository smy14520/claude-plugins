"""Vault scanning: discovery, hidden-dir skipping, page identity."""
from wikicli.index import load_vault


class TestScanning:
    def test_finds_nested_pages(self, vault_of):
        vault = vault_of({"a.md": "x", "notes/deep/b.md": "y"})
        assert [p.path.as_posix() for p in vault.pages] == ["a.md", "notes/deep/b.md"]

    def test_skips_hidden_dirs_and_files(self, make_vault):
        root = make_vault(
            {
                ".forge/issues/x.md": "hidden",
                ".obsidian/note.md": "hidden",
                "keep.md": "visible",
                ".draft.md": "hidden file",
            }
        )
        vault = load_vault(root)
        assert [p.path.as_posix() for p in vault.pages] == ["keep.md"]

    def test_chinese_filename_identity(self, vault_of):
        vault = vault_of({"中文页面.md": "# 中文\n内容"})
        page = vault.pages[0]
        assert page.name == "中文页面"
        assert page.title == "中文"

    def test_title_is_not_identity(self, vault_of):
        vault = vault_of({"foo.md": "# Different Title\n"})
        assert vault.pages[0].name == "foo"

    def test_empty_vault(self, make_vault):
        assert load_vault(make_vault({})).pages == []
