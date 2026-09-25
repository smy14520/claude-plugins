"""体检：死链、孤岛（含豁免与自链）、重复标题（Q14/Q15）。"""

from wikicore.doctor import diagnose
from wikicore.indexer import build_index


def test_dead_link_reported(vault):
    root = vault({"a.md": "指向 [[Missing]]"})
    report = diagnose(build_index(root))
    assert report.dead_links == [("a", "Missing")]
    assert report.blocking


def test_orphan_detected_and_ignorable(vault):
    root = vault({"home.md": "[[other]]", "other.md": "内容", "lonely.md": "内容"})
    index = build_index(root)
    assert diagnose(index).orphans == ["home", "lonely"]
    assert not diagnose(index).blocking
    assert diagnose(index, ignore={"home"}).orphans == ["lonely"]


def test_self_link_does_not_rescue_orphan(vault):
    root = vault({"a.md": "自指 [[a]]"})
    assert diagnose(build_index(root)).orphans == ["a"]


def test_duplicate_title_reported_as_blocking(vault):
    root = vault({"a/X.md": "甲", "b/X.md": "乙"})
    report = diagnose(build_index(root))
    assert report.duplicates == ["X"]
    assert report.blocking


def test_healthy_vault_is_clean(vault):
    root = vault({"a.md": "[[b]]", "b.md": "回 [[a]]"})
    report = diagnose(build_index(root))
    assert report.dead_links == []
    assert report.orphans == []
    assert report.duplicates == []
