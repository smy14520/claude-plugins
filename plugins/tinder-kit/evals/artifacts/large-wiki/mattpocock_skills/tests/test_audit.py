"""体检测试：四类缺陷与「歧义不算死链」的拍板语义。"""

from __future__ import annotations

from wiki_cli import audit, indexer


def run_audit(files):
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return audit.audit(indexer.load(root)[0])


def test_dead_link_reported_with_location():
    report = run_audit({"a.md": "第一行\n[[缺页]]", "b.md": ""})
    (dead,) = report.dead_links
    assert (dead.path, dead.line, dead.raw) == ("a.md", 2, "缺页")


def test_md_suffix_link_still_resolves():
    report = run_audit({"目标.md": "", "a.md": "[[目标.md]]"})
    assert report.dead_links == ()


def test_orphan_is_zero_inlink_only():
    report = run_audit(
        {
            "首页.md": "",  # 零入链：如实报告，不做白名单
            "入链者.md": "[[被链接]]",  # 只有出链、没有入链 → 也是孤岛
            "被链接.md": "",
        }
    )
    assert [p.name for p in report.orphans] == ["入链者", "首页"]


def test_external_links_never_dead_never_inlink():
    report = run_audit(
        {"a.md": "[[https://x.com]]", "b.md": "[[外部页]]", "外部页.md": ""}
    )
    assert report.dead_links == ()
    # a 只有外链（外链不产生入链），b 无人指向 → 两者都是孤岛
    assert [p.name for p in report.orphans] == ["a", "b"]


def test_duplicate_name_reported_links_to_it_not_dead():
    report = run_audit(
        {"x/dup.md": "", "y/dup.md": "", "引用者.md": "[[dup]]"}
    )
    (dup,) = report.duplicates
    assert dup.name == "dup"
    assert dup.paths == ("x/dup.md", "y/dup.md")
    # 歧义目标不算死链：根因已由重名缺陷暴露
    assert report.dead_links == ()


def test_malformed_frontmatter_reported():
    report = run_audit({"a.md": "---\ntags: [x]\n未闭合", "b.md": "---\ntags: [y]\n---\n"})
    (bad,) = report.malformed_frontmatter
    assert bad.rel_path == "a.md"


def test_defect_count_and_clean_report():
    assert run_audit({"a.md": "[[b]]", "b.md": "[[a]]"}).defect_count == 0
    # 死链 + 该页自身零入链（孤岛），两类缺陷同时成立
    report = run_audit({"a.md": "[[缺页]]"})
    assert report.has_defects and report.defect_count == 2
