"""Backward-compatibility shim for test_scenario_runner_checks.py.

Re-exports all functions that the test file uses from the new framework modules.
Also serves as a runnable entry point that forwards to the unified runner.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure framework is importable
_SCENARIO_EVAL_DIR = Path(__file__).resolve().parent
if str(_SCENARIO_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_SCENARIO_EVAL_DIR))

# Re-export from framework modules
from framework.checks import (  # noqa: F401, E402
    _detect_blocking_open_question,
    _has_template_placeholder,
    quality_checks,
)
from framework.phases import (  # noqa: F401, E402
    _is_task_state_ready,
    _derive_impl_started,
    _has_brainstorm_ready_text_marker,
    _derive_review_recorded,
    review_prompt,
    direct_prompt,
    response_timeout_for_phase,
    find_prd,
    read_task_state,
)
from framework.checks import (  # noqa: F401, E402
    slice_progress as _slice_progress,
    derive_review_recorded,
    review_state as _review_state,
)
from framework.runner import extract_result_metrics  # noqa: F401, E402
from framework.reporter import (  # noqa: F401, E402
    aggregate_matrix,
    empty_metrics,
    add_phase_metrics,
    finalize_run_metrics,
    new_run_metrics,
)
from framework.ai_user import fallback_answer  # noqa: F401, E402


if __name__ == "__main__":
    from run import main
    main()
