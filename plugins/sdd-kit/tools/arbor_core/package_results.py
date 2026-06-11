from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .package_checks import validate_functional_checks, validate_impl_checks, validate_slice_checks
from .prd_slices import collect_marker_ids_from_text
from .schema import SLICE_ID_RE, SLICE_STATUSES
from .slice_defs import slice_defs
from .state import add_phase_history, route_package_state

IMPL_RESULT_STATES = {"done", "done_with_concerns", "needs_context", "blocked"}
REVIEW_RESULT_STATES = {"approved", "approved_with_notes", "needs_rework", "brainstorm_drift"}


def _prd_slices_info(pkg: Path, data: dict[str, Any]) -> list:
    """Return materialized slice definitions (parse-once: no prd.md re-parse at runtime)."""
    return slice_defs(pkg, data)


def _acceptance_coverage(pkg: Path, data: dict[str, Any], acceptance: list[str]) -> dict[str, list[str]]:
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
    slices = _prd_slices_info(pkg, data)
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


def _aggregate_slice_evidence(pkg: Path, data: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Aggregate per-slice gate evidence into package-level acceptance/checks/concerns.

    Only usable when every PRD slice has been settled through the mark-slice
    gate (status done with recorded acceptance). Slice-level gate concerns
    (blocked/not_run required checks) are aggregated too, so the thin-summary
    path carries them into the package result. Raises naming the unsettled
    slices and the legal outlets otherwise.
    """
    prd_slices = _prd_slices_info(pkg, data)
    entries = {entry.get("id"): entry for entry in data.get("slices", []) if isinstance(entry, dict)}
    unsettled: list[str] = []
    acceptance: list[str] = []
    checks: list[str] = []
    concerns: list[str] = []
    for slice_item in prd_slices:
        entry = entries.get(slice_item.id)
        if not entry or entry.get("status") != "done" or not entry.get("acceptance"):
            unsettled.append(slice_item.id)
            continue
        acceptance.extend(str(item) for item in entry.get("acceptance", []))
        for check_id in entry.get("checks", []):
            if check_id not in checks:
                checks.append(str(check_id))
        for concern in entry.get("concerns", []):
            if concern not in concerns:
                concerns.append(str(concern))
    if unsettled:
        raise ArborError(
            "record-impl-result 自动聚合失败，以下 slice 未经 mark-slice 结算: "
            + ", ".join(unsettled)
            + "。出路：对每个 slice 用 run-check/record-check 补证据后 "
            'mark-slice --status done --acceptance "<marker-id>: <证据>"；'
            "或显式提供 --acceptance/--check 走手工路径。"
        )
    return acceptance, checks, concerns


def record_impl_result(
    root: Path,
    name: str,
    state: str,
    summary: str,
    acceptance: list[str],
    commands: list[str],
    checks: list[str],
    functional_checks: list[str],
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
    concern_items = [item for item in concerns if item]
    if state in {"done", "done_with_concerns"} and not acceptance_items and not check_items:
        # Thin-summary path: all evidence was settled per slice via the
        # mark-slice gate; aggregate it instead of re-collecting by hand.
        acceptance_items, check_items, slice_concerns = _aggregate_slice_evidence(pkg, data)
        if state == "done" and slice_concerns:
            raise ArborError(
                "以下 slice 带 gate 结算 concerns，DONE 不成立: "
                + "; ".join(slice_concerns)
                + "。出路：--state done_with_concerns 记录（自动聚合 slice concerns），"
                "或补 run-check passed 证据后重新 mark-slice --status done。"
            )
        for item in slice_concerns:
            if item not in concern_items:
                concern_items.append(item)
    result = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "acceptance": acceptance_items,
        "commands": [item for item in commands if item],
        "checks": check_items,
        "concerns": concern_items,
    }
    if state in {"done", "done_with_concerns"}:
        result["acceptance_coverage"] = _acceptance_coverage(pkg, data, acceptance_items)
        check_result = validate_impl_checks(pkg, data, state, check_items, timestamp)
        result["check_coverage"] = check_result["check_coverage"]
        incomplete = check_result["incomplete_required_checks"]
        if incomplete:
            result["incomplete_required_checks"] = incomplete
        functional_result = validate_functional_checks(data, state, [item for item in functional_checks if item])
        result["functional_checks"] = functional_result["functional_checks"]
        incomplete_functional = functional_result["incomplete_functional_checks"]
        if incomplete_functional:
            result["incomplete_functional_checks"] = incomplete_functional
        if state == "done_with_concerns" and not concern_items:
            if incomplete or incomplete_functional:
                raise ArborError(
                    "DONE_WITH_CONCERNS requires --concern describing each verification gap; "
                    "blocked/not_run check reasons are evidence, not the package concern summary."
                )
            raise ArborError("DONE_WITH_CONCERNS requires at least one --concern; use --state done when there are no concerns.")
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


def _slice_marker_coverage(slice_item, acceptance_items: list[str]) -> None:
    """Per-slice gate: every completion marker needs an acceptance reference.

    Same reference rules as _acceptance_coverage, scoped to one slice:
    single-marker slices accept `S-NNN: ...`; multi-marker slices need each
    `S-NNN.M: ...` granularly.
    """
    marker_ids = slice_item.marker_ids()
    coverage: dict[str, list[str]] = {mid: [] for mid in marker_ids}
    suspect_items: list[str] = []
    for item in acceptance_items:
        own_refs = 0
        for ref in collect_marker_ids_from_text(item):
            if ref in coverage:
                coverage[ref].append(item)
                own_refs += 1
            elif ref == slice_item.id:
                if len(marker_ids) == 1:
                    coverage[marker_ids[0]].append(item)
                    own_refs += 1
                # multi-marker: bare id is ambiguous, not counted
        # Items naming at least one own marker may freely mention other slices
        # in prose; an item naming none is a likely marker-id typo.
        if own_refs == 0:
            suspect_items.append(item)
    if suspect_items:
        raise ArborError(
            f"Slice {slice_item.id} 的 acceptance 条目没有引用本 slice 的 marker（疑似 marker id 笔误）: "
            + "; ".join(suspect_items)
            + f"。本 slice 合法引用：{', '.join(marker_ids)}。"
        )
    missing = [mid for mid, items in coverage.items() if not items]
    if missing:
        hints = []
        for mid in missing:
            position = _marker_position(mid) - 1
            if "." in mid and 0 <= position < len(slice_item.completion_markers):
                hints.append(f"{mid} ({slice_item.completion_markers[position]})")
            else:
                hints.append(mid)
        raise ArborError(
            f"Slice {slice_item.id} 不能标记 done，缺 acceptance 引用: "
            + "; ".join(hints)
            + '。出路：每个 marker 一条 --acceptance "<marker-id>: <证据>"；'
            "slice 未完成用 mark-slice --status in_progress --note。"
        )


def mark_slice(
    root: Path,
    name: str,
    slice_id: str,
    status: str,
    note: str,
    actor: str,
    timestamp: str,
    acceptance: list[str] | None = None,
) -> dict[str, Any]:
    if not SLICE_ID_RE.match(slice_id):
        raise ArborError(f"Invalid slice id '{slice_id}'. Use S-001 format.")
    if status not in SLICE_STATUSES:
        raise ArborError(f"Invalid slice status '{status}'. Use: {', '.join(sorted(SLICE_STATUSES))}.")
    pkg, data = load_package(root, name)
    slices_info = _prd_slices_info(pkg, data)
    slice_item = next((item for item in slices_info if item.id == slice_id), None)
    if slice_item is None:
        raise ArborError(f"Slice id '{slice_id}' is not defined in PRD ## Slices.")
    acceptance_items = [item for item in (acceptance or []) if item]
    check_ids: list[str] = []
    slice_concerns: list[str] = []
    if status == "done":
        required_before = data.get("required_checks")
        try:
            _slice_marker_coverage(slice_item, acceptance_items)
            check_ids, slice_concerns = validate_slice_checks(pkg, data, slice_id, timestamp)
        except ArborError:
            # Persist auto-derived required checks even when the gate rejects,
            # so the caller can act on the req ids named in the error.
            if data.get("required_checks") and data.get("required_checks") is not required_before:
                save_package(pkg, data)
            raise
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
        existing = {
            "id": slice_id,
            "status": status,
            "note": note,
            "updated_at": timestamp,
        }
        slices.append(existing)
        slices.sort(key=lambda s: s.get("id", ""))
    if status == "done":
        existing["acceptance"] = acceptance_items
        existing["checks"] = check_ids
        # Recomputed each settle: a re-mark after fixing a blocked check clears stale concerns.
        existing.pop("concerns", None)
        if slice_concerns:
            existing["concerns"] = slice_concerns
    else:
        existing.pop("acceptance", None)
        existing.pop("checks", None)
        existing.pop("concerns", None)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "slice": slice_id, "status": status, "concerns": slice_concerns, "slices": slices}
