"""Shared test fixtures.

Every acceptance entry runs the real CLI as a subprocess with a temporary
directory as its cwd, so the data file is always ``<tmp>/.todos.json`` and each
command is a fresh process (persistence is exercised for real). Store-level
properties (atomic write, schema validation) are tested in-process instead.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

STORE_NAME = ".todos.json"


def console_script() -> str | None:
    """Path to the installed ``todo`` script in the active environment."""
    candidate = Path(sys.executable).with_name("todo")
    return str(candidate) if candidate.is_file() else None


@dataclass(frozen=True)
class Result:
    exit_code: int
    stdout: str
    stderr: str


class Runner:
    """Invoke the ``todo`` console script, falling back to ``python -m``."""

    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self._script = console_script()

    def run(self, *args: str, cwd: Path | None = None) -> Result:
        directory = self.cwd if cwd is None else cwd
        if self._script is None:
            command = [sys.executable, "-m", "todo_cli", *args]
        else:
            command = [self._script, *args]
        completed = subprocess.run(command, cwd=directory, capture_output=True, text=True)
        return Result(completed.returncode, completed.stdout, completed.stderr)

    def __call__(self, *args: str, cwd: Path | None = None) -> Result:
        return self.run(*args, cwd=cwd)


class Store:
    """Read/write access to the data file of one directory."""

    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd

    @property
    def path(self) -> Path:
        return self.cwd / STORE_NAME

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def raw(self) -> bytes:
        return self.path.read_bytes()

    def records(self) -> list[dict]:
        return self.read()["todos"]

    def next_id(self) -> int:
        return self.read()["next_id"]

    def write(self, todos: list[dict], next_id: int | None = None) -> None:
        """Write a document directly, defaulting ``next_id`` past every id used."""
        if next_id is None:
            next_id = max((record["id"] for record in todos), default=0) + 1
        self.path.write_text(
            json.dumps({"next_id": next_id, "todos": todos}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def make_record(
    todo_id: int,
    *,
    title: str = "任务",
    tags: list[str] | None = None,
    priority: str = "med",
    done: bool = False,
    created_at: str = "2026-09-26T08:00:00Z",
    completed_at: str | None = None,
) -> dict:
    """Build one storage record, for tests that seed the file by hand."""
    return {
        "id": todo_id,
        "title": title,
        "tags": list(tags or []),
        "priority": priority,
        "done": done,
        "created_at": created_at,
        "completed_at": completed_at,
    }


@pytest.fixture
def run(tmp_path: Path) -> Runner:
    return Runner(tmp_path)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path)
