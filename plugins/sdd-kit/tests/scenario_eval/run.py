"""
Unified scenario evaluation runner.

Usage:
  # Run a single scenario
  python tests/scenario_eval/run.py --scenario todo-greenfield-small --workflow sdd-full

  # Run comparison (sdd vs direct)
  python tests/scenario_eval/run.py --scenario todo-greenfield-small --workflow sdd-full,direct --repeats 3

  # Run all fixed-request scenarios (regression)
  python tests/scenario_eval/run.py --regression

  # Re-evaluate existing run artifacts
  python tests/scenario_eval/run.py --evaluate-only --run-dir runs/2026-05-10/todo-greenfield-small/

Environment variables:
  ANTHROPIC_API_KEY          - API key for Claude Code CLI (tested agent)
  SCENARIO_TEST_MODEL        - Model for tested agent (default: claude-sonnet-4-6)
  EVAL_AI_USER_KEY           - API key for AI user (default: ANTHROPIC_API_KEY)
  EVAL_AI_USER_MODEL         - Model for AI user (default: claude-sonnet-4-6)
  EVAL_JUDGE_KEY             - API key for evaluator (default: ANTHROPIC_API_KEY)
  EVAL_JUDGE_MODEL           - Model for evaluator (default: claude-sonnet-4-6)
  RUN_SCENARIO_AI_USER       - Must be "1" to run (safety gate)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure the framework package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from framework.config import (
    EnvConfig,
    ScenarioConfig,
    load_env_config,
    load_scenario,
    list_scenarios,
)
from framework.fixtures import (
    PLUGIN_ROOT,
    RUNS_ROOT,
    ScenarioPaths,
    log_event,
    prepare_workdir,
    safe_slug,
    timestamp,
    unique_path,
    write,
)
from framework.runner import (
    PhaseResponse,
    create_direct_client,
    create_sdd_client,
    receive_response,
)
from framework.phases import (
    find_prd,
    read_task_state,
    run_brainstorm_phase,
    run_impl_phase,
    run_review_phase,
    run_direct_phase,
    direct_prompt,
)
from framework.checks import quality_checks, derive_impl_started, slice_progress
from framework.reporter import (
    build_summary,
    capture_diff,
    aggregate_matrix,
    write_aggregate_reports,
    new_run_metrics,
    add_phase_metrics,
    finalize_run_metrics,
)
from framework.evaluator import evaluate_run, EvaluationResult
from framework.ai_user import (
    generate_initial_request,
    generate_answer,
    scripted_answer,
)


def require_enabled() -> None:
    if not os.environ.get("RUN_SCENARIO_AI_USER"):
        raise SystemExit("Set RUN_SCENARIO_AI_USER=1 to run scenario evaluation.")
    try:
        import claude_agent_sdk  # noqa: F401
    except ImportError as exc:
        raise SystemExit("claude-agent-sdk is required. Install with: pip install claude-agent-sdk") from exc


# ---------------------------------------------------------------------------
# Workflow runners
# ---------------------------------------------------------------------------


async def run_sdd_workflow(
    scenario: ScenarioConfig,
    env: EnvConfig,
    paths: ScenarioPaths,
    user_request: str,
    enable_review: bool = False,
    isolate_phases: bool = False,
    group: str | None = None,
    repeat: int | None = None,
) -> dict[str, Any]:
    """Run the full sdd-kit workflow: brainstorm -> impl (-> review)."""
    metrics = new_run_metrics()
    run_error: str | None = None
    impl_loop_entered = False
    review_loop_entered = False

    # Create AI user answer function
    async def ai_user_fn(response_text: str, transcript: list, p: ScenarioPaths, m: dict) -> str:
        if scenario.ai_user_mode == "scripted":
            return scripted_answer(response_text, transcript)
        return await generate_answer(
            question_text=response_text,
            transcript=transcript,
            paths=p,
            profile=scenario.profile,
            project_brief=scenario.project_brief,
            org_context=scenario.org_context,
            api_key=env.ai_user_key,
            model=env.ai_user_model,
            metrics=m,
            base_url=env.ai_user_base_url,
        )

    # Brainstorm phase
    client = create_sdd_client(
        work_dir=paths.work_dir,
        plugin_root=PLUGIN_ROOT,
        model=env.test_model,
        phase="brainstorm",
        log_fn=lambda event, **data: log_event(paths, event, **data),
        api_key=env.anthropic_api_key,
        base_url=env.anthropic_base_url,
    )

    transcript: list[dict[str, Any]] = []
    try:
        await asyncio.wait_for(client.connect(), timeout=scenario.timeouts.connect_timeout)
        log_event(paths, "tested_agent_connected", phase="brainstorm")

        # Build initial prompt
        if scenario.name == "wiki-cross-cut-export-integration":
            prompt = f"用 brainstorm grill-me {user_request}\n\n这个项目已有 `.wiki/`；如果需求涉及已有 module 或 cross-cut 模式，请按 brainstorm skill 先用 `sdd-wiki collect --query \"新增 导出 auth session\" --limit 5 --json` 渐进式查询，不要全量读取 wiki。PRD Technical Framing 应引用实际命中的 cross_cut 页面，核心 scope 保持自包含，并写 wiki 与当前代码不一致时由 impl 逐一识别的 fallback。"
        else:
            prompt = f"用 brainstorm grill-me {user_request}\n\n注意：这是一个全新的空项目目录（{paths.work_dir}），当前没有任何已有 package 或代码。请从零开始 brainstorm，不要假设已有任何历史产物。所有 sdd-arbor 命令和文件操作都必须在当前目录下执行。"

        await asyncio.wait_for(client.query(prompt), timeout=scenario.timeouts.query_timeout)
        log_event(paths, "tested_agent_query_sent", phase="brainstorm", prompt=prompt[:200])

        # Run brainstorm loop
        accumulated_text, transcript, brainstorm_error = await run_brainstorm_phase(
            client=client,
            paths=paths,
            max_turns=scenario.timeouts.brainstorm_turns,
            ai_user_fn=ai_user_fn,
            response_timeout=scenario.timeouts.response_timeout,
            metrics=metrics,
            user_request=user_request,
            scenario_name=scenario.name,
        )
        if brainstorm_error:
            run_error = brainstorm_error

        # Check if ready for impl
        prd_path = find_prd(paths.work_dir)
        task_state = read_task_state(prd_path)
        if task_state and task_state.get("prd", {}).get("status") == "ready":
            if isolate_phases:
                await client.disconnect()
                client = create_sdd_client(
                    work_dir=paths.work_dir,
                    plugin_root=PLUGIN_ROOT,
                    model=env.test_model,
                    phase="impl",
                    log_fn=lambda event, **data: log_event(paths, event, **data),
                    api_key=env.anthropic_api_key,
                    base_url=env.anthropic_base_url,
                )
                await asyncio.wait_for(client.connect(), timeout=scenario.timeouts.connect_timeout)

            # Impl phase
            impl_loop_entered = True
            if hasattr(client, '_phase_state'):
                client._phase_state["current"] = "impl"
            impl_prompt = f"用 impl 执行这个 package PRD：{prd_path.parent.name}" if prd_path else "用 impl 执行当前 ready package"
            if scenario.impl_instruction:
                impl_prompt += f"\n\n{scenario.impl_instruction}"
            await asyncio.wait_for(client.query(impl_prompt), timeout=scenario.timeouts.query_timeout)
            log_event(paths, "tested_agent_query_sent", phase="impl", prompt=impl_prompt)

            impl_text, impl_error = await run_impl_phase(
                client=client,
                paths=paths,
                max_turns=scenario.timeouts.impl_turns,
                response_timeout=scenario.timeouts.response_timeout,
                metrics=metrics,
                prd_path=prd_path,
                scenario_name=scenario.name,
            )
            if impl_error and not run_error:
                run_error = impl_error

            # Review phase (optional)
            if enable_review:
                prd_path = find_prd(paths.work_dir)
                task_state = read_task_state(prd_path)
                if task_state and task_state.get("impl_result"):
                    if isolate_phases:
                        await client.disconnect()
                        client = create_sdd_client(
                            work_dir=paths.work_dir,
                            plugin_root=PLUGIN_ROOT,
                            model=env.test_model,
                            phase="review",
                            log_fn=lambda event, **data: log_event(paths, event, **data),
                            api_key=env.anthropic_api_key,
                            base_url=env.anthropic_base_url,
                        )
                        await asyncio.wait_for(client.connect(), timeout=scenario.timeouts.connect_timeout)

                    review_loop_entered = True
                    review_prompt = f"用 review 审计 package：{prd_path.parent.name}" if prd_path else "用 review 审计当前 package"
                    await asyncio.wait_for(client.query(review_prompt), timeout=scenario.timeouts.query_timeout)
                    log_event(paths, "tested_agent_query_sent", phase="review", prompt=review_prompt)

                    review_text, review_error = await run_review_phase(
                        client=client,
                        paths=paths,
                        max_turns=scenario.timeouts.review_turns,
                        response_timeout=scenario.timeouts.response_timeout,
                        metrics=metrics,
                        prd_path=prd_path,
                    )
                    if review_error and not run_error:
                        run_error = review_error
        else:
            if not run_error:
                run_error = "Brainstorm did not produce a ready package; impl was not started."

    except TimeoutError:
        run_error = run_error or "Timed out waiting for tested agent."
        log_event(paths, "tested_agent_timeout", error=run_error)
    finally:
        await client.disconnect()
        log_event(paths, "tested_agent_disconnected", phase="final")

    # Build summary
    prd_path = find_prd(paths.work_dir)
    prd_text = prd_path.read_text(encoding="utf-8") if prd_path else ""
    task_state = read_task_state(prd_path)
    check_result = quality_checks(prd_text, len(transcript), task_state, paths.work_dir, scenario.name)

    if run_error and check_result["checks"].get("impl_recorded"):
        run_error = None
    elif run_error and check_result["verdict"] == "failed_to_run":
        check_result["verdict"] = "agent_runtime_error"

    diff_info = capture_diff(paths)
    finalize_run_metrics(metrics)

    # AI evaluation
    evaluation_result = None
    if scenario.evaluation.enabled and env.judge_key:
        try:
            dimensions = [{"name": d.name, "prompt": d.prompt, "weight": d.weight} for d in scenario.evaluation.dimensions]
            eval_result = evaluate_run(
                run_dir=paths.run_dir,
                dimensions=dimensions,
                api_key=env.judge_key,
                model=env.judge_model,
                scenario_context=f"场景: {scenario.name}, Profile: {scenario.profile}",
                base_url=env.judge_base_url,
            )
            evaluation_result = {
                "total_score": eval_result.total_score,
                "dimensions": [{"name": d.name, "score": d.score, "reasoning": d.reasoning} for d in eval_result.dimensions],
                "summary": eval_result.summary,
            }
            log_event(paths, "evaluation_complete", score=eval_result.total_score, summary=eval_result.summary)
        except Exception as exc:
            log_event(paths, "evaluation_error", error=str(exc))

    workflow_name = "sdd-review" if enable_review else "sdd-full"
    summary = build_summary(
        paths=paths,
        scenario_name=scenario.name,
        scenario_profile=scenario.profile,
        workflow=workflow_name,
        model=env.test_model,
        ai_user_model=env.ai_user_model,
        ai_user_mode=scenario.ai_user_mode,
        user_request=user_request,
        transcript=transcript,
        task_state=task_state,
        check_result=check_result,
        diff_info=diff_info,
        metrics=metrics,
        run_error=run_error,
        group=group,
        repeat=repeat,
        impl_loop_entered=impl_loop_entered,
        review_loop_entered=review_loop_entered,
        isolate_phases=isolate_phases,
        evaluation_result=evaluation_result,
    )
    write(paths.summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


async def run_direct_workflow(
    scenario: ScenarioConfig,
    env: EnvConfig,
    paths: ScenarioPaths,
    user_request: str,
    group: str | None = None,
    repeat: int | None = None,
) -> dict[str, Any]:
    """Run direct implementation without sdd-kit."""
    metrics = new_run_metrics()
    run_error: str | None = None

    client = create_direct_client(
        work_dir=paths.work_dir,
        model=env.test_model,
        log_fn=lambda event, **data: log_event(paths, event, **data),
        api_key=env.anthropic_api_key,
        base_url=env.anthropic_base_url,
    )

    try:
        await asyncio.wait_for(client.connect(), timeout=scenario.timeouts.connect_timeout)
        log_event(paths, "tested_agent_connected", phase="direct")

        prompt = direct_prompt(user_request)
        await asyncio.wait_for(client.query(prompt), timeout=scenario.timeouts.query_timeout)
        log_event(paths, "tested_agent_query_sent", phase="direct", prompt=prompt[:200])

        direct_text, direct_error = await run_direct_phase(
            client=client,
            paths=paths,
            max_turns=scenario.timeouts.direct_turns,
            response_timeout=scenario.timeouts.response_timeout,
            metrics=metrics,
            user_request=user_request,
        )
        if direct_error:
            run_error = direct_error

    except TimeoutError:
        run_error = "Timed out waiting for tested agent (direct mode)."
        log_event(paths, "tested_agent_timeout", error=run_error)
    finally:
        await client.disconnect()
        log_event(paths, "tested_agent_disconnected", phase="direct")

    diff_info = capture_diff(paths)
    finalize_run_metrics(metrics)

    # AI evaluation
    evaluation_result = None
    if scenario.evaluation.enabled and env.judge_key:
        try:
            dimensions = [{"name": d.name, "prompt": d.prompt, "weight": d.weight} for d in scenario.evaluation.dimensions]
            eval_result = evaluate_run(
                run_dir=paths.run_dir,
                dimensions=dimensions,
                api_key=env.judge_key,
                model=env.judge_model,
                scenario_context=f"场景: {scenario.name}, Profile: {scenario.profile}, Mode: direct (no sdd-kit)",
                base_url=env.judge_base_url,
            )
            evaluation_result = {
                "total_score": eval_result.total_score,
                "dimensions": [{"name": d.name, "score": d.score, "reasoning": d.reasoning} for d in eval_result.dimensions],
                "summary": eval_result.summary,
            }
            log_event(paths, "evaluation_complete", score=eval_result.total_score, summary=eval_result.summary)
        except Exception as exc:
            log_event(paths, "evaluation_error", error=str(exc))

    summary = {
        "run_dir": str(paths.run_dir),
        "work_dir": str(paths.work_dir),
        "workflow": "direct",
        "group": group,
        "repeat": repeat,
        "model": env.test_model,
        "scenario_name": scenario.name,
        "scenario_profile": scenario.profile,
        "user_request": user_request,
        "run_error": run_error,
        "diff": diff_info,
        "metrics": metrics,
        "evaluation": evaluation_result,
        "verdict": "pass" if not run_error else "agent_runtime_error",
    }
    write(paths.summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def run_single(
    scenario: ScenarioConfig,
    env: EnvConfig,
    workflow: str,
    enable_review: bool = False,
    isolate_phases: bool = False,
) -> dict[str, Any]:
    """Run a single scenario with a single workflow."""
    from datetime import datetime

    date = datetime.now().strftime("%Y-%m-%d")
    run_dir = unique_path(RUNS_ROOT / date / safe_slug(f"{scenario.name}-{workflow}"))
    paths = prepare_workdir(run_dir, scenario.fixture, scenario.name, env)

    # Get user request
    if scenario.request_mode == "fixed" and scenario.request_text:
        user_request = scenario.request_text
    else:
        user_request = await generate_initial_request(
            paths=paths,
            profile=scenario.profile,
            project_brief=scenario.project_brief,
            org_context=scenario.org_context,
            api_key=env.ai_user_key,
            model=env.ai_user_model,
            base_url=env.ai_user_base_url,
        )

    log_event(paths, "user_request_resolved", request=user_request[:200])

    if workflow == "direct":
        return await run_direct_workflow(scenario, env, paths, user_request)
    else:
        return await run_sdd_workflow(
            scenario, env, paths, user_request,
            enable_review=enable_review,
            isolate_phases=isolate_phases,
        )


async def run_comparison(
    scenario: ScenarioConfig,
    env: EnvConfig,
    workflows: list[str],
    repeats: int = 1,
    enable_review: bool = False,
    isolate_phases: bool = False,
) -> dict[str, Any]:
    """Run multiple workflows for comparison (matrix mode)."""
    from datetime import datetime

    date = datetime.now().strftime("%Y-%m-%d")
    matrix_dir = unique_path(RUNS_ROOT / date / safe_slug(f"{scenario.name}-matrix"))
    matrix_dir.mkdir(parents=True, exist_ok=True)

    # Resolve user request once (shared across all runs)
    # Use a temporary paths for request generation
    temp_run_dir = matrix_dir / "_temp"
    temp_paths = prepare_workdir(temp_run_dir, scenario.fixture, scenario.name, env)

    if scenario.request_mode == "fixed" and scenario.request_text:
        user_request = scenario.request_text
    else:
        user_request = await generate_initial_request(
            paths=temp_paths,
            profile=scenario.profile,
            project_brief=scenario.project_brief,
            org_context=scenario.org_context,
            api_key=env.ai_user_key,
            model=env.ai_user_model,
            base_url=env.ai_user_base_url,
        )

    # Clean up temp dir
    import shutil
    if temp_run_dir.exists():
        shutil.rmtree(temp_run_dir)

    # Save shared brief
    write(matrix_dir / "brief.md", user_request)
    write(matrix_dir / "matrix.json", json.dumps({
        "scenario": scenario.name,
        "profile": scenario.profile,
        "workflows": workflows,
        "repeats": repeats,
        "model": env.test_model,
        "judge_model": env.judge_model,
    }, ensure_ascii=False, indent=2) + "\n")

    summaries: list[dict[str, Any]] = []
    for rep in range(1, repeats + 1):
        for wf in workflows:
            group = f"{'A' if wf == 'direct' else 'B'}-{wf}"
            run_dir = matrix_dir / group / f"rep-{rep:02d}"
            paths = prepare_workdir(run_dir, scenario.fixture, scenario.name, env)

            if wf == "direct":
                summary = await run_direct_workflow(scenario, env, paths, user_request, group=group, repeat=rep)
            else:
                summary = await run_sdd_workflow(
                    scenario, env, paths, user_request,
                    enable_review=enable_review,
                    isolate_phases=isolate_phases,
                    group=group,
                    repeat=rep,
                )
            summaries.append(summary)
            print_summary(summary)

    aggregate = aggregate_matrix(summaries, scenario.name, scenario.profile)
    write_aggregate_reports(matrix_dir, summaries, aggregate)
    print(f"\nMatrix results: {matrix_dir}")
    return aggregate


async def run_regression(
    env: EnvConfig,
    enable_review: bool = False,
) -> list[dict[str, Any]]:
    """Run all fixed-request scenarios as regression tests."""
    results = []
    for name in list_scenarios():
        scenario = load_scenario(name)
        if scenario.request_mode != "fixed":
            continue
        print(f"\n{'='*60}")
        print(f"Running regression: {name}")
        print(f"{'='*60}")
        summary = await run_single(scenario, env, "sdd-full", enable_review=enable_review)
        results.append(summary)
        print_summary(summary)
    return results


async def run_evaluate_only(run_dir: Path, env: EnvConfig, scenario: ScenarioConfig | None = None) -> dict[str, Any]:
    """Re-evaluate an existing run directory."""
    if scenario is None:
        # Try to load scenario from summary
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            scenario_name = summary.get("scenario_name", "")
            try:
                scenario = load_scenario(scenario_name)
            except FileNotFoundError:
                pass

    if scenario is None or not scenario.evaluation.enabled:
        raise SystemExit("Cannot determine evaluation dimensions. Specify --scenario or ensure scenario has evaluation config.")

    dimensions = [{"name": d.name, "prompt": d.prompt, "weight": d.weight} for d in scenario.evaluation.dimensions]
    result = evaluate_run(
        run_dir=run_dir,
        dimensions=dimensions,
        api_key=env.judge_key,
        model=env.judge_model,
        scenario_context=f"场景: {scenario.name}, Profile: {scenario.profile}",
        base_url=env.judge_base_url,
    )

    eval_output = {
        "total_score": result.total_score,
        "dimensions": [{"name": d.name, "score": d.score, "reasoning": d.reasoning} for d in result.dimensions],
        "summary": result.summary,
        "model": env.judge_model,
        "evaluated_at": timestamp(),
    }
    write(run_dir / "evaluation.json", json.dumps(eval_output, ensure_ascii=False, indent=2) + "\n")
    print(f"Evaluation score: {result.total_score}/5.0")
    print(f"Summary: {result.summary}")
    for d in result.dimensions:
        print(f"  {d.name}: {d.score}/5 — {d.reasoning}")
    return eval_output


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_summary(summary: dict[str, Any]) -> None:
    """Print a concise summary to stdout."""
    verdict = summary.get("verdict", "unknown")
    workflow = summary.get("workflow", "unknown")
    error = summary.get("run_error")
    evaluation = summary.get("evaluation")

    print(f"\n--- {summary.get('scenario_name', '?')} [{workflow}] ---")
    print(f"  Verdict: {verdict}")
    if error:
        print(f"  Error: {error}")
    if evaluation:
        print(f"  AI Score: {evaluation.get('total_score', 'N/A')}/5.0 — {evaluation.get('summary', '')}")
    print(f"  Run dir: {summary.get('run_dir', '?')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SDD-Kit Scenario Evaluation Runner")
    parser.add_argument("--scenario", type=str, help="Scenario name (YAML filename without .yaml)")
    parser.add_argument("--workflow", type=str, default="sdd-full", help="Workflow(s): sdd-full, direct, or comma-separated for comparison")
    parser.add_argument("--repeats", type=int, default=1, help="Number of repeats per workflow")
    parser.add_argument("--enable-review", action="store_true", help="Enable review phase")
    parser.add_argument("--isolate-phases", action="store_true", help="Isolate phases (separate agent sessions)")
    parser.add_argument("--regression", action="store_true", help="Run all fixed-request scenarios")
    parser.add_argument("--evaluate-only", action="store_true", help="Re-evaluate existing run")
    parser.add_argument("--run-dir", type=str, help="Run directory for --evaluate-only")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument("--test-model", type=str, help="Model for tested agent (overrides SCENARIO_TEST_MODEL)")
    parser.add_argument("--ai-user-model", type=str, help="Model for AI user (overrides EVAL_AI_USER_MODEL)")
    parser.add_argument("--judge-model", type=str, help="Model for evaluator (overrides EVAL_JUDGE_MODEL)")
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()

    if args.list:
        scenarios = list_scenarios()
        print("Available scenarios:")
        for name in scenarios:
            scenario = load_scenario(name)
            mode = "fixed" if scenario.request_mode == "fixed" else "ai-gen"
            print(f"  {name} [{scenario.profile}] ({mode})")
        return 0

    if args.evaluate_only:
        env = load_env_config()
        if not args.run_dir:
            raise SystemExit("--evaluate-only requires --run-dir")
        run_dir = Path(args.run_dir)
        if not run_dir.exists():
            raise SystemExit(f"Run directory not found: {run_dir}")
        scenario = load_scenario(args.scenario) if args.scenario else None
        await run_evaluate_only(run_dir, env, scenario)
        return 0

    require_enabled()
    env = load_env_config()

    # CLI model overrides
    if args.test_model or args.ai_user_model or args.judge_model:
        env = EnvConfig(
            anthropic_api_key=env.anthropic_api_key,
            anthropic_base_url=env.anthropic_base_url,
            test_model=args.test_model or env.test_model,
            ai_user_key=env.ai_user_key,
            ai_user_base_url=env.ai_user_base_url,
            ai_user_model=args.ai_user_model or env.ai_user_model,
            judge_key=env.judge_key,
            judge_base_url=env.judge_base_url,
            judge_model=args.judge_model or env.judge_model,
        )

    if args.regression:
        results = await run_regression(env, enable_review=args.enable_review)
        passed = sum(1 for r in results if r.get("verdict") == "pass")
        print(f"\nRegression: {passed}/{len(results)} passed")
        return 0 if passed == len(results) else 1

    if not args.scenario:
        raise SystemExit("Specify --scenario or --regression. Use --list to see available scenarios.")

    scenario = load_scenario(args.scenario)
    workflows = [w.strip() for w in args.workflow.split(",")]

    if len(workflows) > 1 or args.repeats > 1:
        aggregate = await run_comparison(
            scenario, env, workflows,
            repeats=args.repeats,
            enable_review=args.enable_review,
            isolate_phases=args.isolate_phases,
        )
        return 0
    else:
        summary = await run_single(
            scenario, env, workflows[0],
            enable_review=args.enable_review,
            isolate_phases=args.isolate_phases,
        )
        print_summary(summary)
        return 0 if summary.get("verdict") in ("pass", "needs_review") else 1


def main() -> None:
    sys.exit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
