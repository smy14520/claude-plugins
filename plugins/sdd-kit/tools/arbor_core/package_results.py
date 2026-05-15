from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .package_checks import validate_impl_checks
from .prd_slices import collect_marker_ids_from_text, parse_prd_slices
from .schema import SLICE_ID_RE, SLICE_STATUSES
from .state import add_phase_history, route_package_state

IMPL_RESULT_STATES = {"done", "done_with_concerns", "needs_context", "blocked"}
REVIEW_RESULT_STATES = {"approved", "approved_with_notes", "needs_rework", "brainstorm_drift"}


def _prd_slices_info(pkg: Path) -> list:
    """Return PrdSlice list, raising ArborError on parse failure."""
    prd_path = pkg / "prd.md"
    if not prd_path.exists():
        raise ArborError(f"Missing PRD file: {prd_path}")
    slices, errors = parse_prd_slices(prd_path.read_text(encoding="utf-8"))
    if errors:
        raise ArborError("Cannot read PRD slices: " + "; ".join(errors))
    return slices


def _prd_slice_ids(pkg: Path) -> set[str]:
    return {item.id for item in _prd_slices_info(pkg)}


def _acceptance_coverage(pkg: Path, acceptance: list[str]) -> dict[str, list[str]]:
    """Validate acceptance covers every completion marker defined in PRD.

    Marker ids:
    - slice with 1 marker  → `S-NNN`                     (back-compat)
    - slice with N markers → `S-NNN.1`, `S-NNN.2`, ...

    Coverage rules:
    - Single-marker slice: accept either `S-NNN` or `S-NNN.1`.
    - Multi-marker slice: each marker id must appear in at least one acceptance
      entry. Bare `S-NNN` is NOT a shortcut for covering all markers — the
      user chose to list them granularly, so each gets its own evidence.
    - Unknown ids rejected.

    If you really can't cover every marker, use `--state done_with_concerns`
    and document the gap with `--concern`. The CLI still rejects `--state done`
    with missing marker coverage.
    """
    slices = _prd_slices_info(pkg)
    defined_slice_ids = {item.id for item in slices}
    expected_markers: dict[str, list[str]] = {}  # marker_id -> slice_id
    slice_to_markers: dict[str, list[str]] = {}
    for slice_item in slices:
        marker_ids = slice_item.marker_ids()
        slice_to_markers[slice_item.id] = marker_ids
        for mid in marker_ids:
            expected_markers[mid] = slice_item.id

    coverage: dict[str, list[str]] = {mid: [] for mid in expected_markers}
    unknown: set[str] = set()

    for item in acceptance:
        mentioned = collect_marker_ids_from_text(item)
        for ref in mentioned:
            if ref in expected_markers:
                coverage[ref].append(item)
            elif ref in defined_slice_ids:
                # Bare `S-NNN` reference.
                slice_markers = slice_to_markers[ref]
                if len(slice_markers) == 1:
                    # Single-marker slice: bare id is equivalent to the one marker.
                    coverage[slice_markers[0]].append(item)
                # Multi-marker slice: bare id is ambiguous and NOT counted.
                # The impl must reference each marker granularly or switch to
                # done_with_concerns with concern notes.
            else:
                unknown.add(ref)

    if unknown:
        raise ArborError("Impl acceptance references unknown PRD slice/marker ids: " + ", ".join(sorted(unknown)))
    missing = [mid for mid, items in coverage.items() if not items]
    if missing:
        hints = []
        for mid in missing:
            if "." in mid:
                idx = _marker_slice_index(slices, mid)
                pos = _marker_position(mid) - 1
                if 0 <= pos < len(slices[idx].completion_markers):
                    hints.append(f"{mid} ({slices[idx].completion_markers[pos]})")
                    continue
            hints.append(mid)
        raise ArborError("Impl acceptance missing coverage for PRD markers: " + "; ".join(hints))

    # Re-group by slice id for back-compat consumers (module_summary etc.)
    by_slice: dict[str, list[str]] = {slice_id: [] for slice_id in sorted(defined_slice_ids)}
    for mid, items in coverage.items():
        slice_id = expected_markers[mid]
        for entry in items:
            if entry not in by_slice[slice_id]:
                by_slice[slice_id].append(entry)
    return by_slice


def _marker_slice_index(slices: list, marker_id: str) -> int:
    base = marker_id.split(".")[0]
    for i, s in enumerate(slices):
        if s.id == base:
            return i
    return 0


def _marker_position(marker_id: str) -> int:
    try:
        return int(marker_id.split(".")[1])
    except (IndexError, ValueError):
        return 1


def _state_label(state: str) -> str:
    return state.upper()


def record_impl_result(
    root: Path,
    name: str,
    state: str,
    summary: str,
    acceptance: list[str],
    commands: list[str],
    checks: list[str],
    concerns: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if state not in IMPL_RESULT_STATES:
        raise ArborError(f"Invalid impl result state '{state}'.")
    if not summary.strip():
        raise ArborError("Impl result summary is required.")
    pkg, data = load_package(root, name)
    old = data.get("state")
    acceptance_items = [item for item in acceptance if item]
    check_items = [item for item in checks if item]
    result = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "acceptance": acceptance_items,
        "commands": [item for item in commands if item],
        "checks": check_items,
        "concerns": [item for item in concerns if item],
    }
    if state in {"done", "done_with_concerns"}:
        result["acceptance_coverage"] = _acceptance_coverage(pkg, acceptance_items)
        check_result = validate_impl_checks(pkg, data, state, check_items, timestamp)
        result["check_coverage"] = check_result["check_coverage"]
        incomplete = check_result["incomplete_required_checks"]
        if incomplete:
            result["incomplete_required_checks"] = incomplete
    data["impl_result"] = result
    if state in {"done", "done_with_concerns"}:
        route_package_state(data, "done", timestamp, actor, summary.strip())
    elif state == "needs_context":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "brainstorm", "reason": "impl 发现 PRD / technical framing 缺口，需要回 brainstorm 补齐"}
    elif state == "blocked":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "user", "reason": "impl 被环境、权限、依赖或外部因素阻塞，需要用户处理"}
    add_phase_history(data, timestamp, "impl", old, state, actor, summary.strip())
    save_package(pkg, data)
    return {"package": name, "state": state, "impl_result": result, "next_action": data.get("next_action")}


def _append_review_entry(pkg: Path, state: str, summary: str, evidence: list[str], notes: list[str], actor: str, timestamp: str) -> None:
    lines = [
        "",
        f"## {timestamp} {state}",
        "",
        f"- Actor: {actor}",
        f"- Summary: {summary}",
    ]
    for item in evidence:
        lines.append(f"- Evidence: {item}")
    for item in notes:
        lines.append(f"- Note: {item}")
    with (pkg / "review.md").open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def record_review(
    root: Path,
    name: str,
    state: str,
    summary: str,
    evidence: list[str],
    notes: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if state not in REVIEW_RESULT_STATES:
        raise ArborError(f"Invalid review state '{state}'.")
    if not summary.strip():
        raise ArborError("Review summary is required.")
    pkg, data = load_package(root, name)
    old = data.get("state")
    result = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "evidence": [item for item in evidence if item],
        "notes": [item for item in notes if item],
    }
    data["review_result"] = result
    if state in {"approved", "approved_with_notes"}:
        route_package_state(data, "reviewed", timestamp, actor, summary.strip())
    elif state == "needs_rework":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "impl", "reason": "review 要求返工，回到 impl 继续执行"}
    elif state == "brainstorm_drift":
        route_package_state(data, "draft", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "brainstorm", "reason": "review 发现 PRD 漂移，需要回 brainstorm 修正需求"}
    add_phase_history(data, timestamp, "review", old, state, actor, summary.strip())
    save_package(pkg, data)
    _append_review_entry(pkg, state, summary.strip(), [item for item in evidence if item], [item for item in notes if item], actor, timestamp)
    return {"package": name, "state": state, "review_result": result, "next_action": data.get("next_action")}


def mark_slice(
    root: Path,
    name: str,
    slice_id: str,
    status: str,
    note: str,
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if not SLICE_ID_RE.match(slice_id):
        raise ArborError(f"Invalid slice id '{slice_id}'. Use S-001 format.")
    if status not in SLICE_STATUSES:
        raise ArborError(f"Invalid slice status '{status}'. Use: {', '.join(sorted(SLICE_STATUSES))}.")
    pkg, data = load_package(root, name)
    defined_slices = _prd_slice_ids(pkg)
    if slice_id not in defined_slices:
        raise ArborError(f"Slice id '{slice_id}' is not defined in PRD ## Slices.")
    slices = data.get("slices")
    if not isinstance(slices, list):
        slices = []
        data["slices"] = slices
    existing = next((s for s in slices if s.get("id") == slice_id), None)
    if existing:
        existing["status"] = status
        existing["note"] = note
        existing["updated_at"] = timestamp
    else:
        slices.append({
            "id": slice_id,
            "status": status,
            "note": note,
            "updated_at": timestamp,
        })
        slices.sort(key=lambda s: s.get("id", ""))
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "slice": slice_id, "status": status, "slices": slices}
