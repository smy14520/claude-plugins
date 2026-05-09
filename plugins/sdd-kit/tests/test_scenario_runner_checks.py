"""Unit tests for the pure-function helpers in the scenario eval runner.

These tests do not touch the Claude Agent SDK; they only verify the
diagnostic helpers used to derive scenario summaries:

- `_detect_blocking_open_question`: scoped to `## Open Questions` sections
  and respects negated phrasings.
- `_derive_impl_started`: fact-shaped impl detection from `task.json`.
- `_slice_progress`: slice counter and partial-progress indicator.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_EVAL_DIR = PLUGIN_ROOT / "tests" / "scenario_eval"
if str(SCENARIO_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(SCENARIO_EVAL_DIR))

import run_brainstorm_ai_user as runner  # noqa: E402


class DetectBlockingOpenQuestionTests(unittest.TestCase):
    def test_returns_false_when_no_open_questions_section(self):
        prd = "# Demo\n\n## Requirements\n- blocking nothing here\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_chinese_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- 无 blocking open questions。\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_chinese_negation_with_trailing_clause(self):
        """Regression: PRD writers often append rationale after the negation,
        e.g. `无 blocking open question；用户已确认最终摘要`. The detector must
        treat the whole clause as a negation, not just the bare phrase."""
        prd = (
            "# Demo\n\n## Open Questions\n\n"
            "- 无 blocking open question；用户已确认最终摘要，可以 finalize brainstorm。\n"
        )
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_english_negation_with_trailing_clause(self):
        prd = (
            "# Demo\n\n## Open Questions\n\n"
            "- No blocking open questions; user already confirmed final summary.\n"
        )
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_english_no_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- No blocking open questions.\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_none_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- None blocking open questions\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_na_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- N/A blocking open questions\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_not_applicable_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- Not applicable blocking open questions\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_meiyou_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- 没有 blocking open questions。\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_false_for_zanwu_negation(self):
        prd = "# Demo\n\n## Open Questions\n\n- 暂无 blocking open questions。\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_returns_true_for_unresolved_blocking_colon_marker(self):
        prd = "# Demo\n\n## Open Questions\n\n- Blocking: 需要确认支付服务商\n"
        self.assertTrue(runner._detect_blocking_open_question(prd))

    def test_returns_true_for_unresolved_blocking_word_in_section(self):
        prd = "# Demo\n\n## Open Questions\n\n- 是否需要 blocking on auth boundary？\n"
        self.assertTrue(runner._detect_blocking_open_question(prd))

    def test_ignores_blocking_word_outside_open_questions_section(self):
        """Interview Log narrating 'blocking questions' must not trigger a false positive."""
        prd = (
            "# Demo\n\n"
            "## Interview Log\n\n"
            "| Turn | Question | User answer | Requirement change |\n"
            "|---|---|---|---|\n"
            "| 001 | 初始需求 | ... | 确认产品定位、核心能力和首批 blocking 问题 |\n\n"
            "## Open Questions\n\n"
            "- 无 blocking open questions。\n"
        )
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_handles_level_3_heading(self):
        prd = "# Demo\n\n### Open questions\n\n- 无 blocking open questions。\n"
        self.assertFalse(runner._detect_blocking_open_question(prd))

    def test_handles_multiple_open_questions_sections(self):
        prd = (
            "# Demo\n\n"
            "## Open Questions\n\n"
            "- 无 blocking open questions。\n\n"
            "## Requirements\n\n"
            "- something\n\n"
            "### Open questions\n\n"
            "- Blocking: still deciding\n"
        )
        self.assertTrue(runner._detect_blocking_open_question(prd))


class IsTaskStateReadyTests(unittest.TestCase):
    def test_returns_false_for_none(self):
        self.assertFalse(runner._is_task_state_ready(None))

    def test_returns_false_for_empty_dict(self):
        self.assertFalse(runner._is_task_state_ready({}))

    def test_returns_false_when_prd_missing(self):
        self.assertFalse(runner._is_task_state_ready({"state": "ready"}))

    def test_returns_false_when_prd_not_dict(self):
        self.assertFalse(runner._is_task_state_ready({"prd": "ready"}))

    def test_returns_false_when_status_is_draft(self):
        self.assertFalse(
            runner._is_task_state_ready({"prd": {"status": "draft"}})
        )

    def test_returns_true_when_status_is_ready(self):
        self.assertTrue(
            runner._is_task_state_ready({"prd": {"status": "ready"}})
        )


class DeriveImplStartedTests(unittest.TestCase):
    def test_returns_false_for_none_task_state(self):
        self.assertFalse(runner._derive_impl_started(None))

    def test_returns_false_for_empty_task_state(self):
        self.assertFalse(runner._derive_impl_started({}))

    def test_returns_true_when_current_phase_is_impl(self):
        self.assertTrue(runner._derive_impl_started({"current_phase": "impl"}))

    def test_returns_true_when_state_is_doing(self):
        self.assertTrue(runner._derive_impl_started({"state": "doing"}))

    def test_returns_true_when_state_is_done(self):
        self.assertTrue(runner._derive_impl_started({"state": "done"}))

    def test_returns_true_when_impl_result_present(self):
        self.assertTrue(
            runner._derive_impl_started({"impl_result": {"state": "done"}})
        )

    def test_returns_true_when_slice_is_done(self):
        self.assertTrue(
            runner._derive_impl_started(
                {"slices": [{"id": "S-001", "status": "done"}]}
            )
        )

    def test_returns_true_when_slice_is_in_progress(self):
        self.assertTrue(
            runner._derive_impl_started(
                {"slices": [{"id": "S-001", "status": "in_progress"}]}
            )
        )

    def test_returns_false_when_all_slices_pending(self):
        self.assertFalse(
            runner._derive_impl_started(
                {
                    "state": "ready",
                    "current_phase": "brainstorm",
                    "slices": [
                        {"id": "S-001", "status": "pending"},
                        {"id": "S-002", "status": "pending"},
                    ],
                }
            )
        )

    def test_todo_greenfield_small_run_is_reported_as_started(self):
        """Regression: the 2026-05-05 todo-greenfield-small run was wrongly reported as impl_started=false."""
        task_state = {
            "state": "doing",
            "current_phase": "impl",
            "impl_result": None,
            "slices": [
                {"id": "S-001", "status": "done"},
                {"id": "S-002", "status": "done"},
            ],
        }
        self.assertTrue(runner._derive_impl_started(task_state))


class SliceProgressTests(unittest.TestCase):
    def test_returns_zeros_for_none_task_state(self):
        self.assertEqual(
            runner._slice_progress(None),
            {
                "slices_total": 0,
                "slices_done_count": 0,
                "slices_in_progress_count": 0,
                "impl_in_progress": False,
            },
        )

    def test_counts_done_and_in_progress(self):
        task_state = {
            "slices": [
                {"id": "S-001", "status": "done"},
                {"id": "S-002", "status": "done"},
                {"id": "S-003", "status": "in_progress"},
                {"id": "S-004", "status": "pending"},
            ],
            "impl_result": None,
        }
        progress = runner._slice_progress(task_state)
        self.assertEqual(progress["slices_total"], 4)
        self.assertEqual(progress["slices_done_count"], 2)
        self.assertEqual(progress["slices_in_progress_count"], 1)
        self.assertTrue(progress["impl_in_progress"])

    def test_impl_in_progress_false_when_impl_result_recorded(self):
        task_state = {
            "slices": [{"id": "S-001", "status": "done"}],
            "impl_result": {"state": "done"},
        }
        self.assertFalse(runner._slice_progress(task_state)["impl_in_progress"])

    def test_impl_in_progress_false_when_no_slice_activity(self):
        task_state = {
            "slices": [{"id": "S-001", "status": "pending"}],
            "impl_result": None,
        }
        self.assertFalse(runner._slice_progress(task_state)["impl_in_progress"])


class BrainstormReadyTextMarkerTests(unittest.TestCase):
    def test_returns_true_for_finalized_marker(self):
        self.assertTrue(runner._has_brainstorm_ready_text_marker("finalized: demo"))

    def test_returns_true_for_ready_package_written(self):
        self.assertTrue(
            runner._has_brainstorm_ready_text_marker("已定稿并写入 ready package")
        )

    def test_returns_false_for_confirmation_request_with_next_impl_hint(self):
        response = (
            "请确认：是否按这个 PRD 定稿并执行 finalize-brainstorm？"
            "确认后我会把 package 从 draft finalize 为 ready，然后下一步可用 impl 执行。"
        )
        self.assertFalse(runner._has_brainstorm_ready_text_marker(response))


class ResponseTimeoutForPhaseTests(unittest.TestCase):
    def test_defaults_impl_timeout_longer_than_brainstorm(self):
        self.assertEqual(runner.response_timeout_for_phase("brainstorm"), 900)
        self.assertEqual(runner.response_timeout_for_phase("impl"), 2400)

    def test_brainstorm_uses_legacy_response_timeout_fallback(self):
        with mock.patch.dict(
            "os.environ",
            {"SCENARIO_RESPONSE_TIMEOUT": "240"},
            clear=False,
        ):
            self.assertEqual(runner.response_timeout_for_phase("brainstorm"), 240)
            self.assertEqual(runner.response_timeout_for_phase("impl"), 2400)

    def test_phase_specific_env_overrides(self):
        with mock.patch.dict(
            "os.environ",
            {
                "SCENARIO_BRAINSTORM_RESPONSE_TIMEOUT": "300",
                "SCENARIO_IMPL_RESPONSE_TIMEOUT": "1200",
            },
            clear=False,
        ):
            self.assertEqual(runner.response_timeout_for_phase("brainstorm"), 300)
            self.assertEqual(runner.response_timeout_for_phase("impl"), 1200)


class ReviewPromptAndStateTests(unittest.TestCase):
    def test_review_prompt_uses_package_name_from_prd_path(self):
        prd_path = Path("/tmp/project/.arbor/tasks/demo-package/prd.md")
        self.assertEqual(runner.review_prompt(prd_path), "用 review 审计这个 package PRD：demo-package")

    def test_review_prompt_falls_back_to_current_package(self):
        self.assertEqual(runner.review_prompt(None), "用 review 审计当前 package PRD")

    def test_review_recorded_false_for_missing_state(self):
        self.assertFalse(runner._derive_review_recorded(None))
        self.assertFalse(runner._derive_review_recorded({}))

    def test_review_recorded_true_when_review_result_exists(self):
        self.assertTrue(runner._derive_review_recorded({"review_result": {"state": "APPROVED"}}))

    def test_review_state_returns_recorded_state(self):
        self.assertEqual(runner._review_state({"review_result": {"state": "NEEDS_REWORK"}}), "NEEDS_REWORK")
        self.assertIsNone(runner._review_state({"review_result": None}))


class DirectPromptTests(unittest.TestCase):
    def test_direct_prompt_forbids_sdd_workflow_and_followups(self):
        prompt = runner.direct_prompt("做一个本地社区活动管理工具")
        self.assertIn("Do not use sdd-kit skills", prompt)
        self.assertIn("Do not ask follow-up questions", prompt)
        self.assertIn("User brief:", prompt)
        self.assertIn("做一个本地社区活动管理工具", prompt)


class ScriptedFallbackAnswerTests(unittest.TestCase):
    def test_scripted_answer_accepts_recommendation_for_product_questions(self):
        answer = runner.fallback_answer("问题 1：核心对象是什么？我的推荐：任务 + 项目")
        self.assertEqual(answer, "采用推荐。")

    def test_scripted_answer_accepts_letter_a_options_before_finalization(self):
        answer = runner.fallback_answer("请回复 **接受 A** 或取消。")
        self.assertEqual(answer, "接受 A。")

    def test_scripted_answer_confirms_finalization(self):
        self.assertEqual(runner.fallback_answer("请确认是否定稿 finalize"), "确认定稿。")


class MetricsAggregationTests(unittest.TestCase):
    class FakeResult:
        duration_ms = 120
        duration_api_ms = 80
        num_turns = 3
        session_id = "sess-1"
        total_cost_usd = 0.25
        usage = {"input_tokens": 10, "output_tokens": 5}
        stop_reason = "end_turn"

    def test_extract_result_metrics_from_message_like_object(self):
        metrics = runner.extract_result_metrics(self.FakeResult())
        self.assertEqual(metrics["duration_ms"], 120)
        self.assertEqual(metrics["total_cost_usd"], 0.25)
        self.assertEqual(metrics["usage"]["input_tokens"], 10)

    def test_add_phase_metrics_aggregates_cost_duration_and_usage(self):
        bucket = runner.empty_metrics()
        runner.add_phase_metrics(bucket, "impl", {"duration_ms": 100, "total_cost_usd": 0.1, "usage": {"input_tokens": 7}})
        runner.add_phase_metrics(bucket, "impl", {"duration_ms": 50, "total_cost_usd": 0.2, "usage": {"input_tokens": 3}})
        self.assertEqual(bucket["duration_ms"], 150)
        self.assertAlmostEqual(bucket["total_cost_usd"], 0.3)
        self.assertEqual(bucket["usage"]["input_tokens"], 10)
        self.assertEqual(bucket["by_phase"]["impl"]["duration_ms"], 150)

    def test_finalize_run_metrics_reports_combined_totals(self):
        metrics = runner.new_run_metrics()
        runner.add_phase_metrics(metrics["tested_agent"], "direct", {"duration_ms": 100, "total_cost_usd": 0.4})
        runner.add_phase_metrics(metrics["ai_user"], "initial", {"duration_ms": 20, "total_cost_usd": 0.1})
        final = runner.finalize_run_metrics(metrics)
        self.assertEqual(final["harness_total"]["combined_duration_ms"], 120)
        self.assertAlmostEqual(final["harness_total"]["combined_total_cost_usd"], 0.5)


class ExperimentConfigTests(unittest.TestCase):
    def test_parse_experiment_config_supports_phase_isolation(self):
        with mock.patch.dict(
            runner.os.environ,
            {
                "SCENARIO_RUN_MODE": "matrix",
                "SCENARIO_REPEATS": "1",
                "SCENARIO_GROUPS": "A-direct,B-sdd",
                "SCENARIO_ISOLATE_PHASES": "1",
            },
            clear=False,
        ):
            config = runner.parse_experiment_config()
        self.assertTrue(config.enable_review)
        self.assertTrue(config.isolate_phases)
        self.assertEqual(config.groups, ("A-direct", "B-sdd"))


class MatrixAggregationTests(unittest.TestCase):
    def test_matrix_run_dir_labels_groups_and_repeats(self):
        root = Path("/tmp/matrix")
        self.assertEqual(runner.matrix_run_dir(root, "A-direct", 1), root / "A-direct" / "rep-01")
        self.assertEqual(runner.matrix_run_dir(root, "B-sdd", 12), root / "B-sdd" / "rep-12")

    def test_aggregate_matrix_counts_diff_hashes_and_ignores_null_scores(self):
        summaries = [
            {
                "group": "A-direct",
                "verdict": "needs_review",
                "run_error": None,
                "diff": {"sha256": "a", "changed_files": 2},
                "metrics": {"harness_total": {"tested_agent_total_cost_usd": 0.1, "tested_agent_duration_ms": 100}},
                "scores": {"completion": None, "code": 4, "tests": None},
            },
            {
                "group": "A-direct",
                "verdict": "needs_review",
                "run_error": "boom",
                "diff": {"sha256": "a", "changed_files": 4},
                "metrics": {"harness_total": {"tested_agent_total_cost_usd": 0.3, "tested_agent_duration_ms": 300}},
                "scores": {"completion": 3, "code": None, "tests": None},
            },
            {
                "group": "B-sdd",
                "verdict": "pass",
                "semantic_verdict": "APPROVED",
                "run_error": None,
                "diff": {"sha256": "b", "changed_files": 5},
                "metrics": {"harness_total": {"tested_agent_total_cost_usd": 0.5, "tested_agent_duration_ms": 500}},
                "scores": {"completion": None, "code": None, "tests": None},
            },
        ]
        aggregate = runner.aggregate_matrix(summaries)
        self.assertEqual(aggregate["groups"]["A-direct"]["unique_diff_hashes"], 1)
        self.assertEqual(aggregate["groups"]["A-direct"]["runtime_errors"], 1)
        self.assertEqual(aggregate["groups"]["A-direct"]["scores"]["completion"]["count"], 1)
        self.assertEqual(aggregate["groups"]["A-direct"]["scores"]["tests"]["count"], 0)
        self.assertEqual(aggregate["groups"]["B-sdd"]["review_verdict_counts"], {"APPROVED": 1})


class QualityChecksSmokeTests(unittest.TestCase):
    """Spot-check that quality_checks composes correctly with the new helpers."""

    def test_verification_section_counts_as_acceptance_signal(self):
        prd = "# Demo\n\n## 验证重点\n\n- 主路径跑通\n"
        result = runner.quality_checks(prd, turns=1, task_state=None)
        self.assertTrue(result["checks"]["has_acceptance_criteria"])

    def test_blocking_check_uses_section_scoped_detector(self):
        prd = (
            "# Demo\n\n"
            "## Technical Framing\n\n- stack: N/A\n\n"
            "## Slices\n\n"
            "### S-001: first slice\n\n- 完成标志：done\n\n"
            "## Acceptance Criteria\n\n- [ ] works\n\n"
            "## Interview Log\n\n| 001 | ... | ... | 确认首批 blocking 问题 |\n\n"
            "## Open Questions\n\n- 无 blocking open questions。\n"
        )
        result = runner.quality_checks(prd, turns=5, task_state=None)
        self.assertFalse(
            result["checks"]["has_blocking_open_question"],
            "`blocking` in Interview Log must not trigger blocking open question check.",
        )


if __name__ == "__main__":
    unittest.main()
