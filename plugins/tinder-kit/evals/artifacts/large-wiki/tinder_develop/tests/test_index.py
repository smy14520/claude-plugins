"""The .wiki_index.json cache: create, reuse, refresh, self-heal."""
import json

from wikicli.index import INDEX_FILENAME, load_vault


def index_data(root):
    return json.loads((root / INDEX_FILENAME).read_text(encoding="utf-8"))


class TestIndexPersistence:
    def test_creates_index_file(self, make_vault):
        root = make_vault({"a.md": "# A\n[[b]]", "b.md": ""})
        load_vault(root)
        assert (root / INDEX_FILENAME).is_file()
        data = index_data(root)
        assert data["version"] == 1
        assert set(data["pages"]) == {"a.md", "b.md"}
        assert data["pages"]["a.md"]["title"] == "A"

    def test_unchanged_vault_does_not_rewrite(self, make_vault):
        root = make_vault({"a.md": "hello"})
        load_vault(root)
        mtime = (root / INDEX_FILENAME).stat().st_mtime_ns
        vault = load_vault(root)
        assert (root / INDEX_FILENAME).stat().st_mtime_ns == mtime
        assert [p.name for p in vault.pages] == ["a"]

    def test_changed_page_refreshes_index(self, make_vault):
        root = make_vault({"a.md": "old"})
        load_vault(root)
        (root / "a.md").write_text("new [[b]]", encoding="utf-8")
        (root / "b.md").write_text("", encoding="utf-8")
        vault = load_vault(root)
        assert [link.target for link in vault.links_of(vault.pages[0])] == ["b"]
        assert "b.md" in index_data(root)["pages"]

    def test_roundtrip_preserves_parsed_data(self, make_vault):
        content = "---\ntags: [fm]\n---\n# 标题\n#工作 see [[中文页面|别名]]\n"
        root = make_vault({"a.md": content, "中文页面.md": ""})
        first = load_vault(root)
        second = load_vault(root)  # fully served from the cache
        assert [t.tag for t in second.tags_of(second.pages[0])] == [
            t.tag for t in first.tags_of(first.pages[0])
        ]
        assert [l.display for l in second.links_of(second.pages[0])] == ["别名"]
        assert second.pages[0].title == "标题"

    def test_deleted_page_dropped(self, make_vault):
        root = make_vault({"a.md": "", "b.md": ""})
        load_vault(root)
        (root / "b.md").unlink()
        vault = load_vault(root)
        assert [p.name for p in vault.pages] == ["a"]
        assert set(index_data(root)["pages"]) == {"a.md"}

    def test_corrupt_index_self_heals(self, make_vault):
        root = make_vault({"a.md": "[[b]]", "b.md": ""})
        load_vault(root)
        (root / INDEX_FILENAME).write_text("{not json", encoding="utf-8")
        vault = load_vault(root)
        assert len(vault.pages) == 2
        assert index_data(root)["version"] == 1

    def test_foreign_version_rebuilds(self, make_vault):
        root = make_vault({"a.md": "x"})
        (root / INDEX_FILENAME).write_text('{"version": 999, "pages": {}}', encoding="utf-8")
        load_vault(root)
        assert index_data(root)["version"] == 1

    def test_hidden_dirs_never_indexed(self, make_vault):
        root = make_vault({"keep.md": "x", ".obsidian/n.md": "y"})
        vault = load_vault(root)
        assert [p.path.as_posix() for p in vault.pages] == ["keep.md"]
