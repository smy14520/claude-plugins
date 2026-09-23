from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WIKI_TOOL = Path(__file__).resolve().parents[1] / "tools" / "wiki.py"


def _load_wiki():
    spec = importlib.util.spec_from_file_location("forge_wiki", WIKI_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _wiki_root(root: Path) -> Path:
    directory = root / ".forge" / "wiki"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _write_page(path: Path, frontmatter: str, body: str = "# Page\n\nKnowledge.\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")


def _issues(result: dict, level: str, code: str) -> list[dict]:
    return [issue for issue in result[level] if issue["code"] == code]


@pytest.mark.parametrize("missing", ["title", "description", "type"])
def test_required_frontmatter_fields(tmp_path: Path, missing: str):
    wiki = _load_wiki()
    fields = {
        "title": "Required fields",
        "description": "Read when checking the wiki schema.",
        "type": "concept",
    }
    fields.pop(missing)
    frontmatter = "\n".join(f"{key}: {value}" for key, value in fields.items())
    _write_page(_wiki_root(tmp_path) / "concept" / "required.md", frontmatter)

    result = wiki.wiki_lint(tmp_path)

    issues = _issues(result, "errors", "missing_frontmatter")
    assert issues
    assert missing in issues[0]["fields"]


def test_area_is_optional_and_summary_tags_are_warnings(tmp_path: Path):
    wiki = _load_wiki()
    _write_page(
        _wiki_root(tmp_path) / "concept" / "optional.md",
        "title: Optional metadata\ndescription: Read when checking optional wiki metadata.\ntype: concept",
    )

    result = wiki.wiki_lint(tmp_path)

    assert result["ok"] is True
    assert not _issues(result, "errors", "missing_frontmatter")
    assert _issues(result, "warnings", "missing_summary")
    assert _issues(result, "warnings", "missing_tags")


def test_invalid_type_is_an_error(tmp_path: Path):
    wiki = _load_wiki()
    _write_page(
        _wiki_root(tmp_path) / "invalid.md",
        "title: Invalid type\ndescription: Read when validating page types.\ntype: index",
    )

    result = wiki.wiki_lint(tmp_path)

    assert _issues(result, "errors", "invalid_type")


def test_module_context_fields_are_warnings(tmp_path: Path):
    wiki = _load_wiki()
    _write_page(
        _wiki_root(tmp_path) / "module" / "demo.md",
        "title: Demo module\ndescription: Read before changing the demo module.\ntype: module\nsummary: Demo boundary.\ntags: [demo]",
    )

    result = wiki.wiki_lint(tmp_path)

    assert result["ok"] is True
    assert _issues(result, "warnings", "module_missing_package")
    assert _issues(result, "warnings", "module_missing_source_checkpoint")


def test_generated_root_files_are_not_linted(tmp_path: Path):
    wiki = _load_wiki()
    wiki_root = _wiki_root(tmp_path)
    _write_page(
        wiki_root / "concept" / "contract.md",
        "title: Wiki contract\ndescription: Read when maintaining wiki tooling.\ntype: concept\nsummary: Current contract.\ntags: [wiki]",
    )

    assert wiki.main(["--root", str(tmp_path), "index", "--write"]) == 0
    assert (wiki_root / "index.md").is_file()
    assert (wiki_root / "log.md").is_file()

    indexed = wiki.wiki_index(tmp_path)
    result = wiki.wiki_lint(tmp_path)
    generated = {".forge/wiki/index.md", ".forge/wiki/log.md"}
    indexed_paths = {page["path"] for page in indexed["pages"]}
    issue_paths = {issue["path"] for level in ("errors", "warnings") for issue in result[level]}

    assert result["ok"] is True
    assert generated.isdisjoint(indexed_paths)
    assert generated.isdisjoint(issue_paths)


def test_log_records_added_only_on_first_index(tmp_path: Path):
    """log 变更行回归：基线从写入前的 index.md 提取——页面集不变的重跑记 no changes，
    不再全量误记 added（bug：old_stems 曾从 log.md 提取 `- [` 行，恒为空）。"""
    wiki = _load_wiki()
    wiki_root = _wiki_root(tmp_path)
    _write_page(
        wiki_root / "concept" / "stable.md",
        "title: Stable\ndescription: Read when checking log diffing.\ntype: concept\nsummary: s\ntags: [t]",
    )

    assert wiki.main(["--root", str(tmp_path), "index", "--write"]) == 0
    first = (wiki_root / "log.md").read_text(encoding="utf-8")
    assert "1 added: stable.md" in first

    assert wiki.main(["--root", str(tmp_path), "index", "--write"]) == 0
    second = (wiki_root / "log.md").read_text(encoding="utf-8")
    # 新快照在顶部；页面集未变 → 第二行是 no changes，且不新增 added 行
    assert second.splitlines()[1] == "no changes"
    assert second.count("added") == 1  # 仅首次快照的 added 留存


@pytest.mark.parametrize("filename", ["index.md", "log.md"])
def test_nested_generated_name_is_a_content_page(tmp_path: Path, filename: str):
    wiki = _load_wiki()
    nested = _wiki_root(tmp_path) / "concept" / filename
    nested.parent.mkdir(parents=True)
    nested.write_text(f"# Nested {filename}\n", encoding="utf-8")

    indexed = wiki.wiki_index(tmp_path)
    result = wiki.wiki_lint(tmp_path)

    suffix = f"concept/{filename}"
    assert any(page["path"].endswith(suffix) for page in indexed["pages"])
    assert any(issue["path"].endswith(suffix) for issue in _issues(result, "errors", "missing_frontmatter"))


def test_collect_by_files_hits_anchored_pages(tmp_path: Path):
    wiki = _load_wiki()
    directory = _wiki_root(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sync.ts").write_text("export function connect() {}\n", encoding="utf-8")
    _write_page(
        directory / "gotcha" / "safari-disconnect.md",
        "title: Safari 后台断连\ndescription: 标签页进入后台后 websocket 被挂起\ntype: gotcha\ntags: [sync]",
        "# Safari 后台断连\n\n见 `src/sync.ts#connect`。\n",
    )
    _write_page(directory / "concept" / "note.md", "title: Note\ndescription: 笔记实体\ntype: concept")

    by_file = wiki.wiki_collect(tmp_path, None, files=["src/sync.ts"])
    assert [item["path"] for item in by_file["selected"]] == [".forge/wiki/gotcha/safari-disconnect.md"]

    by_dir = wiki.wiki_collect(tmp_path, None, files=["src"])
    assert len(by_dir["selected"]) == 1


def test_search_matches_chinese_substrings(tmp_path: Path):
    wiki = _load_wiki()
    directory = _wiki_root(tmp_path)
    _write_page(directory / "gotcha" / "timeout.md", "title: 三方客服平台超时重试\ndescription: 2 秒超时后指数退避\ntype: gotcha")

    result = wiki.wiki_search(tmp_path, "客服超时")
    assert [item["path"] for item in result["results"]] == [".forge/wiki/gotcha/timeout.md"]


def test_search_requires_query_or_files(tmp_path: Path):
    wiki = _load_wiki()
    _wiki_root(tmp_path)
    with pytest.raises(wiki.WikiError):
        wiki.wiki_search(tmp_path, None)
