"""S-004 -- priorities: stored levels, filtering, and the main-view ordering."""

from __future__ import annotations

from conftest import make_record


def test_add_stores_the_given_priority_and_defaults_to_med(run, store):
    assert run("add", "最急", "-p", "high").exit_code == 0
    assert run("add", "不急", "-p", "low").exit_code == 0
    assert run("add", "没说优先级").exit_code == 0

    levels = {record["title"]: record["priority"] for record in store.records()}
    assert levels == {"最急": "high", "不急": "low", "没说优先级": "med"}

    long_form = run("add", "长参数", "--priority", "high")
    assert long_form.exit_code == 0
    assert store.records()[-1]["priority"] == "high"


def test_default_list_sorts_by_priority_then_id(run, store):
    store.write(
        [
            make_record(1, title="中", priority="med"),
            make_record(2, title="低一", priority="low"),
            make_record(4, title="急二", priority="high"),
            make_record(3, title="急一", priority="high"),
            make_record(5, title="低二", priority="low"),
        ]
    )

    result = run("list")
    assert result.exit_code == 0, result.stderr

    ids = [line.split()[0] for line in result.stdout.splitlines()]
    assert ids == ["#3", "#4", "#1", "#2", "#5"], "high -> med -> low, ties by id ascending"


def test_priority_filter_intersects_with_tag_filter(run, store):
    store.write(
        [
            make_record(1, title="急但不带标签", priority="high"),
            make_record(2, title="急且带标签", tags=["x"], priority="high"),
            make_record(3, title="中且带标签", tags=["x"], priority="med"),
            make_record(4, title="急但已完成", tags=["x"], priority="high", done=True,
                        completed_at="2026-09-26T09:00:00Z"),
        ]
    )

    only_high = run("list", "--priority", "high")
    assert only_high.exit_code == 0
    assert [line.split()[0] for line in only_high.stdout.splitlines()] == ["#1", "#2"]

    high_and_tagged = run("list", "--priority", "high", "--tag", "x")
    assert high_and_tagged.exit_code == 0
    assert high_and_tagged.stdout.splitlines() == ["#2 [ ] high @x 急且带标签"]

    impossible = run("list", "--priority", "high", "--tag", "x", "--tag", "y")
    assert impossible.exit_code == 0
    assert impossible.stdout == "", "stacked filters can legitimately produce nothing"


def test_all_keeps_done_last_while_the_pending_segment_is_priority_sorted(run, store):
    store.write(
        [
            make_record(1, title="低优先在办", priority="low"),
            make_record(2, title="高优先在办", priority="high"),
            make_record(3, title="上午完成", priority="high", done=True,
                        completed_at="2026-09-26T10:00:00Z"),
            make_record(4, title="中午完成", priority="low", done=True,
                        completed_at="2026-09-26T12:00:00Z"),
            make_record(5, title="中优先在办", priority="med"),
        ]
    )

    result = run("list", "--all")
    assert result.exit_code == 0, result.stderr

    ids = [line.split()[0] for line in result.stdout.splitlines()]
    assert ids == ["#2", "#5", "#1", "#4", "#3"], (
        "pending by priority, then every done record newest-first"
    )
    assert "[x]" in result.stdout.splitlines()[3]
    assert "[x]" in result.stdout.splitlines()[4]


def test_add_rejects_an_unknown_priority_level(run, store):
    assert run("add", "已有的一条").exit_code == 0
    baseline = store.raw()

    result = run("add", "x", "-p", "urgent")
    assert result.exit_code != 0, "argparse must refuse an unlisted level"
    assert result.stdout == ""
    assert result.stderr.strip()
    assert store.raw() == baseline

    filtered = run("list", "--priority", "urgent")
    assert filtered.exit_code != 0, "the same vocabulary applies to the filter"


def test_uniform_priority_degenerates_to_id_order(run, store):
    store.write(
        [
            make_record(3, title="三", priority="low"),
            make_record(1, title="一", priority="low"),
            make_record(2, title="二", priority="low"),
        ]
    )

    result = run("list")
    assert result.exit_code == 0

    ids = [line.split()[0] for line in result.stdout.splitlines()]
    assert ids == ["#1", "#2", "#3"], "no priority spread means file order does not leak through"
