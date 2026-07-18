from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WIKI_TOOL = Path(__file__).resolve().parents[1] / "tools" / "wiki.py"


def _load_wiki():
    spec = importlib.util.spec_from_file_location("seed_wiki", WIKI_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _wiki_root(root: Path) -> Path:
    directory = root / ".arbor" / ".wiki"
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
    generated = {".arbor/.wiki/index.md", ".arbor/.wiki/log.md"}
    indexed_paths = {page["path"] for page in indexed["pages"]}
    issue_paths = {issue["path"] for level in ("errors", "warnings") for issue in result[level]}

    assert result["ok"] is True
    assert generated.isdisjoint(indexed_paths)
    assert generated.isdisjoint(issue_paths)


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
