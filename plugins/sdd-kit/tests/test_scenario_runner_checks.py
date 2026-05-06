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
        self.assertEqual(runner.response_timeout_for_phase("brainstorm"), 180)
        self.assertEqual(runner.response_timeout_for_phase("impl"), 1500)

    def test_brainstorm_uses_legacy_response_timeout_fallback(self):
        with mock.patch.dict(
            "os.environ",
            {"SCENARIO_RESPONSE_TIMEOUT": "240"},
            clear=False,
        ):
            self.assertEqual(runner.response_timeout_for_phase("brainstorm"), 240)
            self.assertEqual(runner.response_timeout_for_phase("impl"), 1500)

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


class QualityChecksSmokeTests(unittest.TestCase):
    """Spot-check that quality_checks composes correctly with the new helpers."""

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
