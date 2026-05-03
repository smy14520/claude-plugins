from __future__ import annotations

import re

SCHEMA_VERSION = "arbor-package-v1"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLICE_ID_RE = re.compile(r"^S-\d{3}$")
AMENDMENT_ID_RE = re.compile(r"^AMD-\d{3}$")

PACKAGE_KINDS = {"single"}
TOP_LEVEL_STATES = {
    "draft",
    "ready",
    "doing",
    "done",
    "reviewed",
}
# Legacy states accepted for backward compatibility but routed to new states
LEGACY_STATE_MAP = {
    "planned": "draft",
    "in_progress": "doing",
    "impl_done": "done",
    "needs_context": "doing",
    "blocked": "doing",
    "needs_rework": "doing",
    "brainstorm_drift": "draft",
    "completed": "reviewed",
    "superseded": "reviewed",
}
PHASES = {"brainstorm", "impl", "review", "complete"}
NEXT_ACTION_SKILLS = {"brainstorm", "impl", "review", "user", "none"}
CONTEXT_TYPES = {"impl", "review", "sources"}
CONTEXT_KINDS = {"constraint", "source", "note", "acceptance", "risk", "decision", "file", "command"}
SOURCE_TYPES = {"local-file", "research-note", "external-url", "wiki", "other"}
EXECUTION_STATUSES = {"unclaimed", "in_progress", "done", "reviewed", "pr_open", "merged", "abandoned"}
PR_STATES = {"none", "draft", "open", "merged", "closed", "not_applicable"}
PACKAGE_SIZING_STATUSES = {"unchecked", "fits_package"}
