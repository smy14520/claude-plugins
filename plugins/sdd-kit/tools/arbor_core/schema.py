from __future__ import annotations

import re

SCHEMA_VERSION = "arbor-task-v1"
MAP_SCHEMA_VERSION = "arbor-map-v1"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_ID_RE = re.compile(r"^T-\d{3}$")
AMENDMENT_ID_RE = re.compile(r"^AMD-\d{3}$")
CONTRACT_REQUEST_ID_RE = re.compile(r"^CR-\d{3}$")

MODES = {"strict-atomic", "lean"}
TOP_LEVEL_STATES = {
    "planned",
    "ready",
    "in_progress",
    "needs_context",
    "blocked",
    "impl_done",
    "reviewed",
    "needs_rework",
    "brainstorm_drift",
    "completed",
    "superseded",
}
TASK_STATES = {
    "planned",
    "ready",
    "in_progress",
    "done",
    "done_with_concerns",
    "needs_context",
    "blocked",
    "approved",
    "approved_with_notes",
    "needs_rework",
    "brainstorm_drift",
    "skipped",
}
PHASES = {"brainstorm", "map", "task", "impl", "self_check", "review", "complete"}
PARALLEL_INDEPENDENCE = {"independent", "contract_dependent", "hard_dependent"}
PARALLEL_MAX_PHASES = {"brainstorm", "task", "impl", "review"}
PARALLEL_GATE_PHASES = {"none", "impl", "review"}
CONTRACT_REQUEST_STATUSES = {"open", "accepted", "fulfilled", "rejected", "superseded"}
INTEGRATION_ROLES = {"package", "lead_serial"}
PARALLEL_LANES = {
    "serial_critical_path",
    "parallel_execution",
    "parallel_prep",
    "serial_integration",
    "checkpoint_review",
    "blocked",
    "complete",
}
PARALLEL_STOP_REASONS = {
    "product_decision",
    "permission_required",
    "destructive_action",
    "external_context",
    "unrecoverable_state",
}
PARALLEL_SELF_HEAL_ACTIONS = {
    "export_worker_context",
    "reconcile_package",
    "finish_worker",
    "add_context_batch",
    "upsert_contract",
    "release_stale_claim",
    "regenerate_dispatch",
}
PARALLEL_RUNTIME_EVENTS = {
    "worker_dispatched",
    "worker_worktree_ready",
    "worker_wrong_workspace",
    "worker_waiting_input",
    "worker_blocked",
    "contract_request_proposed",
    "worker_done",
    "worker_stale",
    "worker_shutdown_requested",
    "worker_shutdown_ack",
    "team_cleanup_started",
    "team_cleanup_done",
    "lead_reconcile",
    "lane_switch",
    "self_heal_started",
    "self_heal_done",
    "self_heal_failed",
    "package_reconciled",
    "worker_finished",
    "contract_upserted",
    "stale_claim_released",
    "scheduler_stop",
    "scheduler_continue",
}
NEXT_ACTION_SKILLS = {"brainstorm", "map", "task", "impl", "review", "user", "none"}
CONTEXT_TYPES = {"impl", "review", "sources"}
CONTEXT_KINDS = {"constraint", "source", "note", "acceptance", "risk", "decision", "file", "command"}
SOURCE_TYPES = {"local-file", "research-note", "external-url", "wiki", "task", "other"}
ROLES = {"backend", "frontend", "data", "devops", "shared", "test", "docs", "fullstack"}
EXECUTION_STATUSES = {"unclaimed", "claimed", "released", "worktree_ready", "in_progress", "impl_done", "reviewed", "pr_open", "merged", "abandoned"}
PR_STATES = {"none", "draft", "open", "merged", "closed", "not_applicable"}
AGENT_RECORD_ROLES = {"impl", "review", "test", "validation"}
AGENT_RECORD_STATUSES = {"planned", "running", "passed", "failed", "blocked"}
CHECKPOINT_KINDS = {"worker-reviewed", "lead-integration", "contract-update"}
PACKAGE_SIZING_STATUSES = {"unchecked", "fits_package", "split_recommended", "split_applied"}
CHILD_TASK_EXECUTION_FIELDS = {"branch", "worktree", "pr", "execution"}
DEPENDENCY_COMPLETE_STATES = {"done", "done_with_concerns", "approved", "approved_with_notes", "skipped"}
REVIEW_PASS_STATES = {"approved", "approved_with_notes", "skipped"}