"""S-003 -- tags: repeatable flags, comma equivalence, AND filtering."""

from __future__ import annotations

from conftest import Store, make_record


def test_repeated_flag_and_comma_form_produce_identical_records(run, store):
    separated = store.cwd
    comma = store.cwd / "comma-form"
    comma.mkdir()

    first = run("add", "修登录", "--tag", "backend", "--tag", "urgent", cwd=separated)
    second = run("add", "修登录", "--tag", "backend,urgent", cwd=comma)

    assert first.exit_code == 0, first.stderr
    assert second.exit_code == 0, second.stderr
    assert "#1" in first.stdout and "#1" in second.stdout

    from_separate_flags = store.read()["todos"][0]
    from_comma_list = Store(comma).read()["todos"][0]

    assert from_separate_flags["tags"] == ["backend", "urgent"]
    assert from_comma_list["tags"] == ["backend", "urgent"]
    # created_at is the only field allowed to differ between the two runs.
    from_separate_flags.pop("created_at")
    from_comma_list.pop("created_at")
    assert from_comma_list == from_separate_flags, "the two spellings are one behaviour"


def test_multiple_tags_narrow_with_and_semantics(run, store):
    assert run("add", "只要后端", "--tag", "backend").exit_code == 0
    assert run("add", "后端加急", "--tag", "backend", "--tag", "urgent").exit_code == 0

    both = run("list", "--tag", "backend", "--tag", "urgent")
    assert both.exit_code == 0
    assert both.stdout.splitlines() == ["#2 [ ] med @backend @urgent 后端加急"]

    one = run("list", "--tag", "backend")
    assert [line.split()[0] for line in one.stdout.splitlines()] == ["#1", "#2"]


def test_tag_filter_carries_tags_and_composes_with_all(run, store):
    store.write(
        [
            make_record(1, title="在办的后端", tags=["backend"], priority="high"),
            make_record(2, title="做完的后端", tags=["backend", "docs"], priority="low", done=True,
                        completed_at="2026-09-26T09:00:00Z"),
            make_record(3, title="没标签的", tags=[], priority="med"),
        ]
    )

    pending_only = run("list", "--tag", "backend")
    assert pending_only.exit_code == 0
    assert pending_only.stdout.splitlines() == ["#1 [ ] high @backend 在办的后端"]

    including_done = run("list", "--all", "--tag", "backend")
    assert including_done.exit_code == 0
    assert including_done.stdout.splitlines() == [
        "#1 [ ] high @backend 在办的后端",
        "#2 [x] low @backend @docs 做完的后端",
    ], "--all lifts the pending-only rule, the tag filter still applies"


def test_untagged_todos_never_match_and_empty_result_is_not_an_error(run, store):
    assert run("add", "没有任何标签").exit_code == 0
    assert run("add", "带一个标签", "--tag", "backend").exit_code == 0

    for flag_values in (["--tag", "backend"], ["--tag", "nosuch"]):
        result = run("list", *flag_values)
        assert result.exit_code == 0
        assert "没有任何标签" not in result.stdout, "a tag filter can never match an untagged todo"

    nothing = run("list", "--tag", "nosuch")
    assert nothing.exit_code == 0
    assert nothing.stdout == ""
    assert nothing.stderr == ""


def test_trailing_empty_comma_segment_is_ignored(run, store):
    assert run("add", "修登录", "--tag", "backend").exit_code == 0

    plain = run("list", "--tag", "backend")
    trailing = run("list", "--tag", "backend,")

    assert trailing.exit_code == 0
    assert trailing.stdout == plain.stdout
    assert trailing.stdout.splitlines() == ["#1 [ ] med @backend 修登录"]

    rejected = run("add", "空标签", "--tag", "")
    assert rejected.exit_code != 0, "a --tag value with no tag at all is a usage error"

