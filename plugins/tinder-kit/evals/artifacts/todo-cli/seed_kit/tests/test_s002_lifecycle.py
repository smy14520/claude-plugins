"""S-002 -- lifecycle: done / reopen / rm / clear and the id policy."""

from __future__ import annotations

from conftest import Store, make_record


def test_done_hides_from_default_list_and_stamps_completed_at(run, store):
    assert run("add", "买牛奶").exit_code == 0

    result = run("done", "1")
    assert result.exit_code == 0, result.stderr

    listing = run("list")
    assert listing.exit_code == 0
    assert listing.stdout == "", "the default view is pending only"

    record = store.records()[0]
    assert record["done"] is True
    assert record["completed_at"] is not None
    assert record["created_at"] is not None

    everything = run("list", "--all")
    assert everything.exit_code == 0
    assert "#1" in everything.stdout


def test_all_puts_done_after_pending_in_reverse_completion_order(run, store):
    store.write(
        [
            make_record(1, title="旧的活", priority="med"),
            make_record(2, title="新的活", priority="med"),
            make_record(3, title="先做完的", done=True, completed_at="2026-09-26T10:00:05Z"),
            make_record(4, title="后做完的", done=True, completed_at="2026-09-26T11:00:00Z"),
        ]
    )

    result = run("list", "--all")
    assert result.exit_code == 0, result.stderr

    ids = [line.split()[0] for line in result.stdout.splitlines()]
    assert ids == ["#1", "#2", "#4", "#3"], "pending first by id, then done newest-first"
    done_lines = [line for line in result.stdout.splitlines() if "#3" in line or "#4" in line]
    assert all("[x]" in line for line in done_lines), "done rows carry a completion marker"


def test_done_records_completed_in_the_same_second_break_ties_by_id_descending(run, store):
    store.write(
        [
            make_record(5, title="先记的", done=True, completed_at="2026-09-26T10:00:00Z"),
            make_record(7, title="后记的", done=True, completed_at="2026-09-26T10:00:00Z"),
        ]
    )

    result = run("list", "--all")
    assert result.exit_code == 0, result.stderr
    assert [line.split()[0] for line in result.stdout.splitlines()] == ["#7", "#5"], (
        "same-second completions fall back to id descending"
    )


def test_remove_drops_one_record_and_does_not_recycle_the_id(run, store):
    assert run("add", "第一条").exit_code == 0
    assert run("add", "第二条").exit_code == 0

    removed = run("rm", "2")
    assert removed.exit_code == 0, removed.stderr

    everything = run("list", "--all")
    assert everything.exit_code == 0
    assert "#2" not in everything.stdout
    assert "#1" in everything.stdout
    assert [record["id"] for record in store.records()] == [1]

    again = run("add", "第三条")
    assert again.exit_code == 0
    assert "#3" in again.stdout, "the id of a removed todo is never handed out again"
    assert store.next_id() == 4


def test_reopen_returns_to_pending_and_keeps_every_other_field(run, store):
    assert run("add", "修登录", "--tag", "backend,urgent", "-p", "high").exit_code == 0
    before = dict(store.records()[0])

    assert run("done", "1").exit_code == 0
    done_record = store.records()[0]
    assert done_record["done"] is True and done_record["completed_at"]

    reopened = run("reopen", "1")
    assert reopened.exit_code == 0, reopened.stderr

    listing = run("list")
    assert listing.exit_code == 0
    assert "#1" in listing.stdout, "reopened todos are back in the default view"

    after = store.records()[0]
    assert after["done"] is False
    assert after["completed_at"] is None
    assert after["title"] == before["title"]
    assert after["tags"] == before["tags"] == ["backend", "urgent"]
    assert after["priority"] == before["priority"] == "high"
    assert after["created_at"] == before["created_at"]


def test_add_after_purging_everything_continues_the_persisted_counter(run, store):
    # rm path: delete the last remaining record by hand
    for title in ("一", "二"):
        assert run("add", title).exit_code == 0
    assert run("rm", "1").exit_code == 0
    assert run("rm", "2").exit_code == 0
    assert store.records() == []

    assert run("add", "三").exit_code == 0
    assert [record["id"] for record in store.records()] == [3], "rm'd ids stay retired"
    assert store.next_id() == 4

    # clear path: same directory wiped with clear instead
    other = store.cwd / "clear-purge"
    other.mkdir()
    for title in ("一", "二"):
        assert run("add", title, cwd=other).exit_code == 0
    assert run("done", "1", cwd=other).exit_code == 0
    assert run("done", "2", cwd=other).exit_code == 0
    assert run("clear", cwd=other).exit_code == 0

    assert run("add", "三", cwd=other).exit_code == 0
    cleared_store = Store(other)
    cleared = [record["id"] for record in cleared_store.records()]
    assert cleared == [3], "clear must not rewind the counter either"
    assert cleared_store.next_id() == 4


def test_done_rejects_an_unknown_id_and_touches_nothing(run, store):
    store.write([make_record(1, title="在办的")])
    baseline = store.raw()

    result = run("done", "99")
    assert result.exit_code != 0
    assert result.stdout == ""
    assert result.stderr.strip(), "the failure must be explained on stderr"
    assert store.raw() == baseline


def test_rm_rejects_an_unknown_id_and_touches_nothing(run, store):
    store.write([make_record(1, title="在办的")])
    baseline = store.raw()

    result = run("rm", "99")
    assert result.exit_code != 0
    assert result.stdout == ""
    assert result.stderr.strip()
    assert store.raw() == baseline, "rm is not silently idempotent"


def test_reopen_rejects_pending_and_unknown_ids(run, store):
    store.write([make_record(1, title="还没做完")])
    baseline = store.raw()

    pending = run("reopen", "1")
    assert pending.exit_code != 0
    assert pending.stdout == ""
    assert pending.stderr.strip()
    assert store.raw() == baseline

    missing = run("reopen", "99")
    assert missing.exit_code != 0
    assert missing.stderr.strip()
    assert store.raw() == baseline
