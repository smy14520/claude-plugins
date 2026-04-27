from __future__ import annotations

import re

SCHEMA_VERSION = "arbor-task-v1"
MAP_SCHEMA_VERSION = "arbor-map-v1"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_ID_RE = re.compile(r"^T-\d{3}$")
AMENDMENT_ID_RE = re.compile(r"^AMD-\d{3}$")

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