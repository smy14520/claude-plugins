"""Phase execution logic for scenario evaluation runs."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Callable

from .fixtures import ScenarioPaths, append_dialogue, log_event, write_jsonl
from .reporter import add_phase_metrics
from .runner import PhaseResponse, receive_response


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


def find_prd(work_dir: Path) -> Path | None:
    """Find the most recently modified .arbor/tasks/*/prd.md file."""
    prd_files = list(work_dir.glob(".arbor/tasks/*/prd.md"))
    if not prd_files:
        return None
    # Return the most recently modified prd.md (likely the one being actively worked on)
    return max(prd_files, key=lambda p: p.stat().st_mtime)


def read_task_state(prd_path: Path | None) -> dict[str, Any] | None:
    """Read task.json sibling to a prd.md file."""
    if prd_path is None:
        return None
    task_path = prd_path.with_name("task.json")
    if not task_path.exists():
        return None
    return json.loads(task_path.read_text(encoding="utf-8"))


def _is_task_state_ready(task_state: dict[str, Any] | None) -> bool:
    """Whether durable package state has advanced to prd.status == 'ready'."""
    if not task_state:
        return False
    prd = task_state.get("prd")
    if not isinstance(prd, dict):
        return False
    return prd.get("status") == "ready"


def _has_brainstorm_ready_text_marker(response_text: str) -> bool:
    """Detect finalization text markers in agent response."""
    lowered = response_text.lower()
    return (
        "finalized:" in lowered
        or "已定稿并写入 ready package" in response_text
        or "已定稿为 ready package" in response_text
        or "package 已 ready" in response_text
        or "ready package 已写入" in response_text
    )


_IMPL_ACTIVE_SLICE_STATES = frozenset({"doing", "in_progress", "done"})


def _derive_impl_started(task_state: dict[str, Any] | None) -> bool:
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


def _derive_review_recorded(task_state: dict[str, Any] | None) -> bool:
    """Whether review_result has been recorded."""
    return bool(task_state and task_state.get("review_result"))


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------


async def run_brainstorm_phase(
    client: Any,
    paths: ScenarioPaths,
    max_turns: int,
    ai_user_fn: Callable[..., Any],
    response_timeout: int,
    metrics: dict[str, Any],
    user_request: str,
    scenario_name: str,
) -> tuple[str, list[dict[str, Any]], str | None]:
    """Run brainstorm phase.

    Returns (accumulated_text, transcript, error_or_none).
    """
    transcript: list[dict[str, Any]] = []
    accumulated_text = ""
    error: str | None = None

    for turn_index in range(1, max_turns + 1):
        phase_response = await receive_response(client, response_timeout)

        if phase_response.metrics:
            add_phase_metrics(metrics.setdefault("tested_agent", {}), "brainstorm", phase_response.metrics)

        if phase_response.error:
            error = phase_response.error
            break

        # Check durable state
        prd_path_probe = find_prd(paths.work_dir)
        task_state_probe = read_task_state(prd_path_probe)
        task_state_ready = _is_task_state_ready(task_state_probe)

        response_text = phase_response.text

        if not response_text:
            if task_state_ready:
                append_dialogue(
                    paths,
                    "Brainstorm 完成",
                    "[break reason: task_state_ready_empty_response]",
                )
                log_event(
                    paths,
                    "brainstorm_ready_detected",
                    reason="task_state_ready_empty_response",
                )
                break
            error = "Tested agent returned an empty brainstorm response."
            break

        accumulated_text += response_text
        text_ready_marker = _has_brainstorm_ready_text_marker(response_text)

        if text_ready_marker or task_state_ready:
            break_reason = "text_marker" if text_ready_marker else "task_state_ready"
            append_dialogue(
                paths,
                "Brainstorm 完成",
                f"[break reason: {break_reason}]\n\n{response_text}",
            )
            log_event(paths, "brainstorm_ready_detected", reason=break_reason)
            break

        # Get AI user answer
        answer = await ai_user_fn(response_text, transcript, paths, metrics)
        entry = {
            "phase": "brainstorm",
            "turn": len(transcript) + 1,
            "question": response_text,
            "answer": answer,
        }
        transcript.append(entry)
        write_jsonl(paths.transcript_path, entry)
        append_dialogue(
            paths,
            f"Brainstorm Turn {entry['turn']}",
            f"### 被测 agent\n\n{response_text}\n\n### AI user\n\n{answer}",
        )
        log_event(paths, "ai_user_conversation_answer", turn=entry["turn"], answer=answer)

        # Send followup
        await asyncio.wait_for(
            client.query(answer),
            timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")),
        )
        log_event(paths, "tested_agent_followup_sent", phase="brainstorm", turn=entry["turn"])

    return accumulated_text, transcript, error


async def run_impl_phase(
    client: Any,
    paths: ScenarioPaths,
    max_turns: int,
    response_timeout: int,
    metrics: dict[str, Any],
    prd_path: Path | None,
    scenario_name: str,
) -> tuple[str, str | None]:
    """Run impl phase.

    Returns (accumulated_text, error_or_none).
    """
    accumulated_text = ""
    error: str | None = None

    for impl_turn in range(1, max_turns + 1):
        phase_response = await receive_response(client, response_timeout)

        if phase_response.metrics:
            add_phase_metrics(metrics.setdefault("tested_agent", {}), "impl", phase_response.metrics)

        if phase_response.error:
            error = phase_response.error
            break

        response_text = phase_response.text
        if not response_text:
            error = "Tested agent returned an empty impl response."
            break

        accumulated_text += response_text
        append_dialogue(paths, f"Impl response {impl_turn}", response_text)

        # Check if impl_result recorded
        current_prd = find_prd(paths.work_dir)
        task_state = read_task_state(current_prd)
        if task_state and task_state.get("impl_result"):
            break

        # Check for done markers in response text
        lowered = response_text.lower()
        if any(marker in lowered for marker in (
            "done_with_concerns", "needs_context", "blocked", "record-impl-result",
        )):
            break

        if impl_turn >= max_turns:
            error = "Impl reached max response turns without recorded impl_result."
            break

        # Send continuation prompt
        await asyncio.wait_for(
            client.query(
                "继续执行 impl，按 PRD Slices 完成剩余工作；不要询问我，遇到问题按 impl skill 记录结果。"
            ),
            timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")),
        )
        log_event(paths, "tested_agent_followup_sent", phase="impl", turn=impl_turn)

    return accumulated_text, error


async def run_review_phase(
    client: Any,
    paths: ScenarioPaths,
    max_turns: int,
    response_timeout: int,
    metrics: dict[str, Any],
    prd_path: Path | None,
) -> tuple[str, str | None]:
    """Run review phase.

    Returns (accumulated_text, error_or_none).
    """
    accumulated_text = ""
    error: str | None = None

    for review_turn in range(1, max_turns + 1):
        phase_response = await receive_response(client, response_timeout)

        if phase_response.metrics:
            add_phase_metrics(metrics.setdefault("tested_agent", {}), "review", phase_response.metrics)

        if phase_response.error:
            error = phase_response.error
            break

        response_text = phase_response.text
        if not response_text:
            error = "Tested agent returned an empty review response."
            break

        accumulated_text += response_text
        append_dialogue(paths, f"Review response {review_turn}", response_text)

        # Check if review_result recorded
        current_prd = find_prd(paths.work_dir)
        task_state = read_task_state(current_prd)
        if _derive_review_recorded(task_state):
            break

        if review_turn >= max_turns:
            error = "Review reached max response turns without recorded review_result."
            break

        # Send continuation prompt
        await asyncio.wait_for(
            client.query(
                "继续执行 review 审计并用 sdd-arbor record-review 记录 verdict；不要修改代码。"
            ),
            timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")),
        )
        log_event(paths, "tested_agent_followup_sent", phase="review", turn=review_turn)

    return accumulated_text, error


async def run_direct_phase(
    client: Any,
    paths: ScenarioPaths,
    max_turns: int,
    response_timeout: int,
    metrics: dict[str, Any],
    user_request: str,
) -> tuple[str, str | None]:
    """Run direct implementation (no sdd-kit).

    Returns (accumulated_text, error_or_none).
    """
    accumulated_text = ""
    error: str | None = None

    for turn in range(1, max_turns + 1):
        phase_response = await receive_response(client, response_timeout)

        if phase_response.metrics:
            add_phase_metrics(metrics.setdefault("tested_agent", {}), "direct", phase_response.metrics)

        if phase_response.error:
            error = phase_response.error
            break

        response_text = phase_response.text
        if not response_text:
            error = "Tested agent returned an empty direct response."
            break

        accumulated_text += response_text
        append_dialogue(paths, f"Direct response {turn}", response_text)

        # Direct mode: single response is typically sufficient
        # Break after first substantive response
        break

    return accumulated_text, error


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def review_prompt(prd_path: Path | None) -> str:
    """Build the review phase prompt."""
    if prd_path:
        return f"用 review 审计这个 package PRD：{prd_path.parent.name}"
    return "用 review 审计当前 package PRD"


def direct_prompt(user_request: str) -> str:
    """Build the direct implementation prompt (no sdd-kit)."""
    return f"""Implement this user brief directly in the current project.
Do not use sdd-kit skills, brainstorm, impl, review, .arbor, or PRD workflow.
Do not ask follow-up questions; make reasonable assumptions and keep scope tight.
Write/update code and tests as needed. Run relevant verification if feasible.
End with a concise Direct result summary including files changed, tests run, and concerns.

User brief:
{user_request}""".strip()


def response_timeout_for_phase(phase: str) -> int:
    """Get the response timeout for a given phase from env vars."""
    if phase == "impl":
        return int(os.environ.get("SCENARIO_IMPL_RESPONSE_TIMEOUT", "2400"))
    if phase == "direct":
        return int(os.environ.get("SCENARIO_DIRECT_RESPONSE_TIMEOUT", "2400"))
    if phase == "review":
        return int(os.environ.get("SCENARIO_REVIEW_RESPONSE_TIMEOUT", "1800"))
    return int(
        os.environ.get(
            "SCENARIO_BRAINSTORM_RESPONSE_TIMEOUT",
            os.environ.get("SCENARIO_RESPONSE_TIMEOUT", "900"),
        )
    )
