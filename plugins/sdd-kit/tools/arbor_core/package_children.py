from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError


def add_slice(root: Path, parent: str, child_package: str, title: str, scope: str, acceptance: str, slice_id: str | None, timestamp: str) -> dict[str, Any]:
    raise ArborError("Package splitting has been removed; write ordered work in PRD ## Slices instead.")


def materialize_children(root: Path, parent: str, timestamp: str) -> dict[str, Any]:
    raise ArborError("Package splitting has been removed; impl executes PRD ## Slices in one package.")


def parent_check(root: Path, parent: str, timestamp: str) -> dict[str, Any]:
    raise ArborError("parent-check has been removed; use sdd-arbor show/list and PRD ## Slices for progress.")
