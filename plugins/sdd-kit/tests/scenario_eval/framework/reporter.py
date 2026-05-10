"""Report generation for scenario evaluation runs."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fixtures import ScenarioPaths, write, timestamp


def capture_diff(paths: ScenarioPaths, max_bytes: int = 2_000_000) -> dict[str, Any]:
    """Capture git diff and status from the work directory."""
    env = {"GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
           "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid"}
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=paths.work_dir,
        capture_output=True, text=True, check=False, env={**__import__("os").environ, **env},
    ).stdout
    # Stage all changes (including untracked files) so diff --cached captures everything
    subprocess.run(
        ["git", "add", "-A"], cwd=paths.work_dir,
        capture_output=True, check=False, env={**__import__("os").environ, **env},
    )
    stat = subprocess.run(
        ["git", "diff", "--cached", "--stat"], cwd=paths.work_dir,
        capture_output=True, text=True, check=False, env={**__import__("os").environ, **env},
    ).stdout
    patch_result = subprocess.run(
        ["git", "diff", "--cached"], cwd=paths.work_dir,
        capture_output=True, text=True, check=False, env={**__import__("os").environ, **env},
    )
    patch = patch_result.stdout
    truncated = False
    if len(patch.encode("utf-8")) > max_bytes:
        patch = patch[:max_bytes].rsplit("\n", 1)[0]
        truncated = True
    write(paths.run_dir / "git_status.txt", status)
    write(paths.run_dir / "diff.patch", patch)
    return {
        "sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest() if patch else None,
        "stat": stat,
        "changed_files": sum(1 for line in status.splitlines() if line.strip()),
        "patch_path": "diff.patch",
        "truncated": truncated,
    }


def build_summary(
    paths: ScenarioPaths,
    scenario_name: str,
    scenario_profile: str,
    workflow: str,
    model: str,
    ai_user_model: str,
    ai_user_mode: str,
    user_request: str,
    transcript: list[dict[str, Any]],
    task_state: dict[str, Any] | None,
    check_result: dict[str, Any],
    diff_info: dict[str, Any],
    metrics: dict[str, Any],
    run_error: str | None = None,
    group: str | None = None,
    repeat: int | None = None,
    impl_loop_entered: bool = False,
    review_loop_entered: bool = False,
    isolate_phases: bool = False,
    evaluation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the summary dict for a completed run."""
    from .checks import derive_impl_started, slice_progress, derive_review_recorded, review_state

    impl_result = task_state.get("impl_result") if task_state else None
    review_result_data = task_state.get("review_result") if task_state else None

    summary = {
        "run_dir": str(paths.run_dir),
        "work_dir": str(paths.work_dir),
        "workflow": workflow,
        "phase_isolation": isolate_phases,
        "group": group,
        "repeat": repeat,
        "model": model,
        "ai_user_model": ai_user_model,
        "ai_user_mode": ai_user_mode,
        "scenario_name": scenario_name,
        "scenario_profile": scenario_profile,
        "user_request": user_request,
        "turns": len(transcript),
        "impl_started": derive_impl_started(task_state),
        "impl_loop_entered": impl_loop_entered,
        "review_loop_entered": review_loop_entered,
        "review_recorded": derive_review_recorded(task_state),
        "review_state": review_state(task_state),
        "semantic_verdict": review_state(task_state),
        **slice_progress(task_state),
        "run_error": run_error,
        "impl_result": impl_result,
        "review_result": review_result_data,
        "verdict": check_result["verdict"],
        "checks": check_result["checks"],
        "diff": diff_info,
        "scores": {},
        "metrics": metrics,
        "timestamp": timestamp(),
    }
    if evaluation_result:
        summary["evaluation"] = evaluation_result
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    """Print a human-readable summary to stdout."""
    print(f"\n{'='*60}")
    print(f"Scenario: {summary.get('scenario_name')}")
    print(f"Verdict: {summary.get('verdict')}")
    print(f"Workflow: {summary.get('workflow')}")
    if summary.get("evaluation"):
        eval_data = summary["evaluation"]
        print(f"AI Score: {eval_data.get('total_score', 'N/A')}/5")
    print(f"Turns: {summary.get('turns')}")
    print(f"Slices: {summary.get('slices_done_count', 0)}/{summary.get('slices_total', 0)}")
    if summary.get("run_error"):
        print(f"Error: {summary['run_error']}")
    cost = summary.get("metrics", {}).get("harness_total", {}).get("combined_total_cost_usd")
    if cost:
        print(f"Cost: ${cost:.2f}")
    print(f"Run dir: {summary.get('run_dir')}")
    print(f"{'='*60}\n")


def aggregate_matrix(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate results from multiple runs into statistical summary."""
    by_group: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        by_group.setdefault(summary.get("group") or "unknown", []).append(summary)

    groups: dict[str, Any] = {}
    for group, items in sorted(by_group.items()):
        costs = [item.get("metrics", {}).get("harness_total", {}).get("tested_agent_total_cost_usd") for item in items]
        durations = [item.get("metrics", {}).get("harness_total", {}).get("tested_agent_duration_ms") for item in items]
        changed_files = [item.get("diff", {}).get("changed_files") for item in items]
        eval_scores = [item.get("evaluation", {}).get("total_score") for item in items]

        groups[group] = {
            "runs": len(items),
            "runtime_errors": sum(1 for item in items if item.get("run_error")),
            "verdict_counts": _count_values(item.get("verdict") for item in items),
            "unique_diff_hashes": len({item.get("diff", {}).get("sha256") for item in items if item.get("diff", {}).get("sha256")}),
            "tested_agent_cost_usd": _numeric_stats([float(v) for v in costs if isinstance(v, (int, float))]),
            "tested_agent_duration_ms": _numeric_stats([float(v) for v in durations if isinstance(v, (int, float))]),
            "changed_files": _numeric_stats([float(v) for v in changed_files if isinstance(v, (int, float))]),
            "eval_scores": _numeric_stats([float(v) for v in eval_scores if isinstance(v, (int, float))]),
        }

    scenario_name = summaries[0].get("scenario_name", "unknown") if summaries else "unknown"
    scenario_profile = summaries[0].get("scenario_profile", "unknown") if summaries else "unknown"
    return {"scenario": scenario_name, "profile": scenario_profile, "runs": len(summaries), "groups": groups}


def write_aggregate_reports(matrix_dir: Path, summaries: list[dict[str, Any]], aggregate: dict[str, Any]) -> None:
    """Write aggregate.json and aggregate.md to the matrix directory."""
    write(matrix_dir / "aggregate.json", json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"# Scenario Matrix Aggregate — {aggregate.get('scenario', 'unknown')}",
        "",
        "| Group | Runs | Verdicts | Errors | Unique diffs | Cost mean | Eval score mean |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for group, data in aggregate["groups"].items():
        lines.append(
            f"| {group} | {data['runs']} | {json.dumps(data['verdict_counts'], ensure_ascii=False)} "
            f"| {data['runtime_errors']} | {data['unique_diff_hashes']} "
            f"| {data['tested_agent_cost_usd'].get('mean', 'N/A')} "
            f"| {data['eval_scores'].get('mean', 'N/A')} |"
        )
    write(matrix_dir / "aggregate.md", "\n".join(lines) + "\n")


def _numeric_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "pstdev": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 4),
        "pstdev": round(statistics.pstdev(values), 4) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
    }


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------


def empty_metrics() -> dict[str, Any]:
    return {"by_phase": {}, "total_cost_usd": 0.0, "duration_ms": 0, "usage": {}}


def merge_usage(left: dict[str, Any], right: Any) -> dict[str, Any]:
    result = dict(left)
    if not isinstance(right, dict):
        return result
    for key, value in right.items():
        if isinstance(value, (int, float)):
            result[key] = result.get(key, 0) + value
        elif isinstance(value, dict):
            result[key] = merge_usage(result.get(key, {}), value)
    return result


def add_phase_metrics(bucket: dict[str, Any], phase: str, metrics: dict[str, Any]) -> None:
    if not metrics:
        return
    phases = bucket.setdefault("by_phase", {})
    phase_metrics = phases.setdefault(phase, {})
    for key, value in metrics.items():
        if key == "usage" and isinstance(value, dict):
            phase_metrics[key] = merge_usage(phase_metrics.get(key, {}), value)
            bucket["usage"] = merge_usage(bucket.get("usage", {}), value)
        elif key in {"duration_ms", "duration_api_ms", "num_turns"} and isinstance(value, (int, float)):
            phase_metrics[key] = phase_metrics.get(key, 0) + value
            if key == "duration_ms":
                bucket[key] = bucket.get(key, 0) + value
        elif key == "total_cost_usd" and isinstance(value, (int, float)):
            phase_metrics[key] = phase_metrics.get(key, 0.0) + value
            bucket[key] = bucket.get(key, 0.0) + value
        else:
            phase_metrics[key] = value


def new_run_metrics() -> dict[str, Any]:
    return {"tested_agent": empty_metrics(), "ai_user": empty_metrics(), "harness_total": {}}


def finalize_run_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    tested = metrics.get("tested_agent", {})
    ai_user = metrics.get("ai_user", {})
    metrics["harness_total"] = {
        "tested_agent_total_cost_usd": tested.get("total_cost_usd", 0.0),
        "tested_agent_duration_ms": tested.get("duration_ms", 0),
        "ai_user_total_cost_usd": ai_user.get("total_cost_usd", 0.0),
        "ai_user_duration_ms": ai_user.get("duration_ms", 0),
        "combined_total_cost_usd": tested.get("total_cost_usd", 0.0) + ai_user.get("total_cost_usd", 0.0),
        "combined_duration_ms": tested.get("duration_ms", 0) + ai_user.get("duration_ms", 0),
    }
    return metrics
