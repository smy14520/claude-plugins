"""S-005 -- maintenance and scripting: edit / clear / --json."""

from __future__ import annotations

import json

from conftest import make_record

FIELDS = {"id", "title", "tags", "priority", "done", "created_at", "completed_at"}


def test_edit_changes_only_the_fields_it_was_given(run, store):
    assert run("add", "原标题", "--tag", "backend", "-p", "high").exit_code == 0
    before = dict(store.records()[0])

    result = run("edit", "1", "--title", "新标题", "-p", "low")
    assert result.exit_code == 0, result.stderr

    after = store.records()[0]
    assert after["title"] == "新标题"
    assert after["priority"] == "low"
    assert after["id"] == before["id"] == 1
    assert after["tags"] == before["tags"] == ["backend"]
    assert after["created_at"] == before["created_at"]
    assert after["done"] is False
    assert after["completed_at"] is None
    assert store.next_id() == 2, "edit never consumes an id"


def test_edit_replaces_tags_wholesale_and_leaves_done_records_alone(run, store):
    assert run("add", "要改标签的", "--tag", "old1", "--tag", "old2").exit_code == 0

    replaced = run("edit", "1", "--tag", "x", "--tag", "y")
    assert replaced.exit_code == 0, replaced.stderr
    assert store.records()[0]["tags"] == ["x", "y"], "--tag replaces the whole set"

    untouched = run("edit", "1", "--title", "换个标题")
    assert untouched.exit_code == 0
    assert store.records()[0]["tags"] == ["x", "y"], "an edit without --tag keeps tags"
    assert store.records()[0]["title"] == "换个标题"

    assert run("done", "1").exit_code == 0
    done_before = dict(store.records()[0])
    edited_done = run("edit", "1", "--tag", "z", "-p", "med")
    assert edited_done.exit_code == 0, "edit works on completed todos too"

    after = store.records()[0]
    assert after["done"] is True
    assert after["completed_at"] == done_before["completed_at"]
    assert after["tags"] == ["z"]
    assert after["priority"] == "med"

    comma_form = run("edit", "1", "--tag", "a,b,c")
    assert comma_form.exit_code == 0
    assert store.records()[0]["tags"] == ["a", "b", "c"]


def test_clear_deletes_completed_and_keeps_pending_in_order(run, store):
    store.write(
        [
            make_record(1, title="在办一", priority="med"),
            make_record(2, title="在办二", priority="high"),
            make_record(3, title="完成一", priority="low", done=True,
                        completed_at="2026-09-26T09:00:00Z"),
            make_record(4, title="在办三", priority="low"),
            make_record(5, title="完成二", priority="med", done=True,
                        completed_at="2026-09-26T10:00:00Z"),
        ]
    )
    before = run("list")
    assert before.exit_code == 0

    cleared = run("clear")
    assert cleared.exit_code == 0, cleared.stderr
    assert [record["id"] for record in store.records()] == [1, 2, 4]
    assert all(record["done"] is False for record in store.records())

    after = run("list")
    assert after.exit_code == 0
    assert after.stdout == before.stdout, "the pending view survives clear untouched"
    assert store.next_id() == 6, "clear never rewinds the counter"


def test_clear_with_nothing_completed_hints_on_stderr_and_keeps_the_file(run, store):
    assert run("add", "只有未完成").exit_code == 0
    baseline = store.raw()

    result = run("clear")
    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr.strip(), "the user is told there was nothing to do"
    assert store.raw() == baseline


def test_json_view_is_the_same_result_as_the_text_view(run, store):
    store.write(
        [
            make_record(1, title="甲", tags=["x"], priority="low"),
            make_record(2, title="乙", tags=["x", "y"], priority="high"),
            make_record(3, title="丙", tags=["x"], priority="med", done=True,
                        completed_at="2026-09-26T11:00:00Z"),
        ]
    )

    text = run("list", "--all", "--tag", "x")
    payload = run("list", "--all", "--tag", "x", "--json")

    assert payload.exit_code == 0, payload.stderr
    assert payload.stderr == ""
    todos = json.loads(payload.stdout)
    assert isinstance(todos, list), "stdout must be pure JSON, no prose around it"
    text_ids = [line.split()[0] for line in text.stdout.splitlines()]
    assert [record["id"] for record in todos] == [int(item.lstrip("#")) for item in text_ids]
    assert todos == [store.records()[1], store.records()[0], store.records()[2]], (
        "elements are the stored records, in the text view's order"
    )
    assert all(set(record) == FIELDS for record in todos)

    narrowed = run("list", "--json", "--priority", "high", "--tag", "y")
    assert json.loads(narrowed.stdout) == [store.records()[1]]

    default_view = run("list", "--json")
    assert json.loads(default_view.stdout) == [store.records()[1], store.records()[0]]


def test_json_view_of_an_empty_result_is_a_bare_array(run, store):
    assert run("add", "不匹配的", "--tag", "backend").exit_code == 0

    filtered = run("list", "--tag", "nosuch", "--json")
    assert filtered.exit_code == 0
    assert filtered.stdout.strip() == "[]", "no text, no header, just an empty array"
    assert json.loads(filtered.stdout) == []

    empty_directory = store.cwd / "no-file"
    empty_directory.mkdir()
    fresh = run("list", "--json", cwd=empty_directory)
    assert fresh.exit_code == 0
    assert fresh.stdout.strip() == "[]"
    assert not (empty_directory / ".todos.json").exists(), "still no file created by a read"


def test_edit_rejects_an_unknown_id(run, store):
    store.write([make_record(1, title="在办的")])
    baseline = store.raw()

    result = run("edit", "99", "--title", "不该生效")
    assert result.exit_code != 0
    assert result.stdout == ""
    assert result.stderr.strip()
    assert store.raw() == baseline


def test_edit_without_any_field_is_a_no_op(run, store):
    store.write([make_record(1, title="在办的", tags=["a"], priority="high")])
    baseline = store.raw()

    result = run("edit", "1")
    assert result.exit_code == 0, result.stderr
    assert store.raw() == baseline, "no flags means nothing is written"
