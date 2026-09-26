"""S-001 -- tracer bullet: add -> persist -> list, and the storage boundaries."""

from __future__ import annotations

import json
import os
import re
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from todo_cli import store

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: UTC ISO 8601 with a trailing Z, second precision, exactly as specified.
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

FIELDS = {"id", "title", "tags", "priority", "done", "created_at", "completed_at"}


def as_utc(stamp: str) -> datetime:
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")


def test_add_reports_id_and_persists_complete_record(run, store):
    before = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    result = run("add", "买牛奶")
    after = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=1)

    assert result.exit_code == 0, result.stderr
    assert "#1" in result.stdout
    assert result.stderr == ""

    assert store.exists(), "add must create ./.todos.json"
    document = store.read()
    assert document["next_id"] == 2
    assert len(document["todos"]) == 1

    record = document["todos"][0]
    assert set(record) == FIELDS, "record shape is frozen in S-001"
    assert record["id"] == 1
    assert record["title"] == "买牛奶"
    assert record["tags"] == []
    assert record["priority"] == "med", "add defaults to med"
    assert record["done"] is False
    assert record["completed_at"] is None, "pending means completed_at is null"
    assert TIMESTAMP.match(record["created_at"])
    assert before <= as_utc(record["created_at"]) <= after, "created_at is UTC wall clock"


def test_list_from_a_new_process_sees_what_add_wrote(run, store):
    assert run("add", "买牛奶").exit_code == 0
    second = run("add", "写周报")

    assert second.exit_code == 0
    assert "#2" in second.stdout, "ids increment across processes"

    listing = run("list")
    assert listing.exit_code == 0
    assert listing.stderr == ""
    lines = listing.stdout.splitlines()
    assert len(lines) == 2
    assert "#1" in lines[0] and "买牛奶" in lines[0]
    assert "#2" in lines[1] and "写周报" in lines[1]
    assert store.next_id() == 3


def test_help_shows_command_surface_and_runtime_has_no_dependencies(run):
    top = run("--help")
    assert top.exit_code == 0
    assert "add" in top.stdout
    assert "list" in top.stdout

    for command in ("add", "list"):
        subcommand = run(command, "--help")
        assert subcommand.exit_code == 0
        assert "usage" in subcommand.stdout

    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["dependencies"] == [], "runtime must stay dependency-free"
    assert config["project"]["scripts"]["todo"] == "todo_cli.cli:main"
    assert config["project"]["requires-python"].startswith(">=3.12")


def test_add_rejects_blank_title_and_leaves_the_file_alone(run, store):
    assert run("add", "先记一条").exit_code == 0
    baseline = store.raw()

    rejected = run("add", "")
    assert rejected.exit_code != 0
    assert rejected.stdout == ""
    assert rejected.stderr.strip(), "the rejection must be explained on stderr"
    assert store.raw() == baseline

    blank = run("add", "   ")
    assert blank.exit_code != 0
    assert store.raw() == baseline


def test_list_without_a_data_file_is_empty_and_creates_nothing(run, store):
    result = run("list")

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not store.exists(), "reads never create the file, only writes do"


def test_save_keeps_the_original_document_when_the_replace_step_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    on_disk = tmp_path / ".todos.json"
    store.save(
        {
            "next_id": 2,
            "todos": [
                {
                    "id": 1,
                    "title": "买牛奶",
                    "tags": [],
                    "priority": "med",
                    "done": False,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": None,
                }
            ],
        }
    )
    baseline = on_disk.read_bytes()

    def exploding_replace(src, dst):
        raise OSError("replace failed mid-flight")

    monkeypatch.setattr(os, "replace", exploding_replace)
    with pytest.raises(OSError):
        store.save(
            {
                "next_id": 3,
                "todos": [
                    {
                        "id": 1,
                        "title": "changed underneath",
                        "tags": [],
                        "priority": "high",
                        "done": False,
                        "created_at": "2026-09-26T08:00:00Z",
                        "completed_at": None,
                    }
                ],
            }
        )

    # still inside tmp_path: the read path must parse exactly what survived
    assert store.load()["todos"][0]["title"] == "买牛奶"
    assert on_disk.read_bytes() == baseline, (
        "a failed replace must not damage the previous document"
    )
    assert isinstance(json.loads(on_disk.read_text(encoding="utf-8")), dict)
    assert not (tmp_path / ".todos.json.tmp").exists(), "no temp file left behind"
