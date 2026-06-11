"""Deterministic quality checks for scenario evaluation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_SLICE_HEADER_PATTERN = re.compile(r"^### S-\d{3}:", re.MULTILINE)
_LEGACY_SLICE_CHECKBOX_PATTERN = re.compile(r"^- \[[ x\-]\] S-\d{3}", re.MULTILINE)
_SLICE_SCAFFOLD_TOKENS = (
    "<walking skeleton 或第一个独立可验证的契约/功能>",
    "<walking skeleton 或第一个独立可验证的行为>",
    "<扩展某个契约/功能/行为/状态转换>",
    "<下一个独立可验证的行为>",
    "<回归 / 边界 / 自检切片>",
    "<完成后多了什么可独立验证的契约/功能/行为>",
    "Impl 只更新 [ ] / [-] / [x]",
)
_TEMPLATE_PLACEHOLDER_RE = re.compile(r"<([^>\n]+)>")
_ALLOWED_ANGLE_BRACKET_TOKENS = {"noun", "输入"}
_IMPL_ACTIVE_SLICE_STATES = frozenset({"doing", "in_progress", "done"})
_OPEN_QUESTIONS_SECTION_RE = re.compile(
    r"^#{2,}\s*Open [Qq]uestions\b.*?(?=^#{2,}\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
_NEGATIVE_BLOCKING_RE = re.compile(
    r"^\s*-?\s*(?:无|暂无|没有|not\s+applicable|n/?a|none|no)\s+(?:any\s+)?blocking\s+open\s+questions?\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
_BLOCKING_WORD_RE = re.compile(r"(?:^|[^a-zA-Z-])blocking", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _has_template_placeholder(prd_text: str) -> bool:
    """Check if PRD contains unfilled template placeholders."""
    for match in _TEMPLATE_PLACEHOLDER_RE.finditer(prd_text):
        token = match.group(1).strip()
        if token in _ALLOWED_ANGLE_BRACKET_TOKENS:
            continue
        return True
    return False


def _detect_blocking_open_question(prd_text: str) -> bool:
    """Scan only within `## Open Questions` sections for a non-negated blocking reference.

    Any PRD discussion of `blocking` outside Open Questions (e.g. Interview Log
    narrating "confirmed first batch of blocking questions") must not trigger this check.
    """
    sections = [m.group(0) for m in _OPEN_QUESTIONS_SECTION_RE.finditer(prd_text)]
    if not sections:
        return False
    joined = "\n".join(sections)
    filtered = _NEGATIVE_BLOCKING_RE.sub("", joined)
    if "Blocking:" in filtered:
        return True
    return bool(_BLOCKING_WORD_RE.search(filtered))


def _read_text_if_exists(path: Path) -> str:
    """Safe file read returning empty string if missing."""
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _wiki_integration_checks(work_dir: Path, prd_text: str, scenario_name: str) -> dict[str, bool]:
    """Run wiki-specific integration checks."""
    if scenario_name != "wiki-cross-cut-export-integration":
        return {}

    events_text = _read_text_if_exists(work_dir.parent / "events.jsonl")
    dialogue_text = _read_text_if_exists(work_dir.parent / "dialogue.md")
    combined_trace = events_text + "\n" + dialogue_text
    prd_has_wikilink = "[[CrossCut/新增导出]]" in prd_text or "[[新增导出]]" in prd_text
    service_text = _read_text_if_exists(work_dir / "services/auth/exports.py")
    routes_text = _read_text_if_exists(work_dir / "api/auth_routes.py")
    registry_text = _read_text_if_exists(work_dir / "registry/export_registry.py")
    tests_text = _read_text_if_exists(work_dir / "tests/test_auth_exports.py")
    all_wiki_pages = list((work_dir / ".wiki").rglob("*.md")) if (work_dir / ".wiki").exists() else []
    read_wiki_count = sum(1 for page in all_wiki_pages if page.as_posix() in combined_trace)

    return {
        "wiki_brainstorm_collect_used": "sdd-wiki collect" in combined_trace and "新增" in combined_trace and "导出" in combined_trace,
        "wiki_prd_references_cross_cut": prd_has_wikilink,
        "wiki_prd_has_fallback": prd_has_wikilink and ("fallback" in prd_text.lower() or "与现状不一致" in prd_text or "逐一识别" in prd_text),
        "wiki_prd_scope_self_contained": all(token in prd_text for token in ("session", "Session", "EXPORT_REGISTRY")) and "/api/auth/session/export" in prd_text,
        "wiki_trace_not_blind_read_all": read_wiki_count < len(all_wiki_pages) if all_wiki_pages else False,
        "wiki_impl_service_updated": "auth_export_user_session" in service_text and "token" in service_text,
        "wiki_impl_route_updated": "/api/auth/session/export" in routes_text and "auth_export_user_session" in routes_text,
        "wiki_impl_registry_updated": "auth.session" in registry_text and "auth_export_user_session" in registry_text,
        "wiki_impl_tests_updated": "auth_export_user_session" in tests_text and "auth.session" in tests_text,
    }


def slice_progress(task_state: dict[str, Any] | None) -> dict[str, Any]:
    """Extract slice progress metrics from task state."""
    slices = (task_state or {}).get("slices") or []
    total = len(slices)
    done = sum(1 for s in slices if s.get("status") == "done")
    in_progress = sum(1 for s in slices if s.get("status") in ("doing", "in_progress"))
    impl_result = (task_state or {}).get("impl_result")
    return {
        "slices_total": total,
        "slices_done_count": done,
        "slices_in_progress_count": in_progress,
        "impl_in_progress": bool((done > 0 or in_progress > 0) and not impl_result),
    }


def derive_impl_started(task_state: dict[str, Any] | None) -> bool:
    """Whether impl has started based on task state."""
    if not task_state:
        return False
    if task_state.get("current_phase") == "impl":
        return True
    state = task_state.get("state", "")
    if state in ("doing", "done"):
        return True
    if task_state.get("impl_result"):
        return True
    slices = task_state.get("slices") or []
    return any(s.get("status") in _IMPL_ACTIVE_SLICE_STATES for s in slices)


def derive_review_recorded(task_state: dict[str, Any] | None) -> bool:
    """Whether review_result has been recorded."""
    return bool(task_state and task_state.get("review_result"))


def review_state(task_state: dict[str, Any] | None) -> str | None:
    """Extract review_result.state string."""
    if not task_state:
        return None
    review_result = task_state.get("review_result")
    if not review_result:
        return None
    return review_result.get("state")


# ---------------------------------------------------------------------------
# Main quality checks
# ---------------------------------------------------------------------------


def quality_checks(
    prd_text: str,
    turns: int,
    task_state: dict[str, Any] | None = None,
    work_dir: Path | None = None,
    scenario_name: str = "",
    scenario_profile: str = "",
) -> dict[str, Any]:
    """Run deterministic quality checks on scenario output."""
    has_slice_headers = bool(_SLICE_HEADER_PATTERN.search(prd_text))
    has_completion_markers = "完成标志" in prd_text
    has_legacy_slice_checkboxes = bool(_LEGACY_SLICE_CHECKBOX_PATTERN.search(prd_text))
    has_slice_scaffold = any(tok in prd_text for tok in _SLICE_SCAFFOLD_TOKENS)

    checks: dict[str, Any] = {
        "multi_turn": turns >= 3 or scenario_name == "wiki-cross-cut-export-integration",
        "has_technical_framing": "Technical Framing" in prd_text,
        "has_slices": (
            "## Slices" in prd_text
            and has_slice_headers
            and has_completion_markers
            and not has_legacy_slice_checkboxes
            and not has_slice_scaffold
        ),
        "has_legacy_slice_checkboxes": has_legacy_slice_checkboxes,
        "has_slice_scaffold": has_slice_scaffold,
        "has_acceptance_criteria": "Acceptance Criteria" in prd_text or "验收" in prd_text or "验证重点" in prd_text,
        "has_existing_code_anchor": (
            True if scenario_profile.startswith("greenfield-")
            else "现有" in prd_text or "existing" in prd_text.lower() or "src/" in prd_text or "services/" in prd_text
        ),
        "has_template_placeholder": _has_template_placeholder(prd_text),
        "has_blocking_open_question": _detect_blocking_open_question(prd_text),
        "package_ready": bool(task_state and task_state.get("prd", {}).get("status") == "ready"),
        "impl_recorded": bool(task_state and task_state.get("impl_result")),
    }

    if work_dir is not None:
        checks.update(_wiki_integration_checks(work_dir, prd_text, scenario_name))

    # Determine verdict
    hard_pass = (
        checks["multi_turn"]
        and checks["has_technical_framing"]
        and checks["has_slices"]
        and checks["has_acceptance_criteria"]
        and checks["has_existing_code_anchor"]
    )

    if scenario_name == "wiki-cross-cut-export-integration":
        hard_pass = hard_pass and all(
            checks.get(key)
            for key in (
                "wiki_brainstorm_collect_used",
                "wiki_prd_references_cross_cut",
                "wiki_prd_has_fallback",
                "wiki_prd_scope_self_contained",
                "wiki_trace_not_blind_read_all",
                "wiki_impl_service_updated",
                "wiki_impl_route_updated",
                "wiki_impl_registry_updated",
                "wiki_impl_tests_updated",
            )
        )

    if not prd_text:
        verdict = "failed_to_run"
    elif (
        hard_pass
        and checks["package_ready"]
        and checks["impl_recorded"]
        and not checks["has_template_placeholder"]
        and not checks["has_blocking_open_question"]
    ):
        verdict = "pass"
    elif hard_pass:
        verdict = "needs_review"
    elif scenario_name == "wiki-cross-cut-export-integration" and any(
        checks.get(key)
        for key in (
            "wiki_brainstorm_collect_used",
            "wiki_prd_references_cross_cut",
            "wiki_impl_service_updated",
        )
    ):
        verdict = "needs_review"
    else:
        verdict = "failed"

    return {"verdict": verdict, "checks": checks}
