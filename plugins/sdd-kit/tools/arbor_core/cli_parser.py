"""Argument parser for the sdd-arbor CLI.

Command surface policy: PUBLIC_COMMANDS is the skill-facing contract; internal
commands stay hidden from --help and exist for plumbing/recovery only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .package_checks import CHECK_STATUSES
from .schema import *

PUBLIC_COMMANDS = (
    "finalize-brainstorm",
    "validate",
    "doctor",
    "set-status",
    "impl-packet",
    "mark-slice",
    "derive-required-checks",
    "run-check",
    "record-check",
    "record-impl-result",
    "record-review",
    "add-amendment",
    "add-context",
    "module-summary",
    "list",
    "show",
)


def _public_command(sub: argparse._SubParsersAction, name: str, **kwargs) -> argparse.ArgumentParser:
    return sub.add_parser(name, **kwargs)


def _internal_command(sub: argparse._SubParsersAction, name: str, help_text: str) -> argparse.ArgumentParser:
    parser = sub.add_parser(name, help=help_text, description=help_text)
    sub._choices_actions = [action for action in sub._choices_actions if getattr(action, "dest", None) != name]
    parser.set_defaults(internal_command=True)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage sdd-kit Arbor PRD-first packages.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root containing .arbor/.")
    parser.add_argument("--now", help="Override timestamp for deterministic tests.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    public_commands = ", ".join(PUBLIC_COMMANDS)
    sub = parser.add_subparsers(dest="command", required=True, metavar="{" + public_commands + "}")

    finalize_parser = _public_command(
        sub,
        "finalize-brainstorm",
        help="Finalize PRD + package boundary from one JSON object.",
        description="Finalize a brainstorm PRD into ready Arbor package state.",
        epilog=(
            "JSON schema:\n"
            "  {\"name\"|\"package\": \"pkg-name\", \"kind\": \"single\", \"prd\"|\"prd_path\": \"...\", \"title\"?: \"...\", \"decision\"?: \"...\"}\n"
            "Use prd_path for an existing .arbor/tasks/<package>/prd.md draft. Large scopes use PRD ## Slices."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    finalize_input = finalize_parser.add_mutually_exclusive_group(required=True)
    finalize_input.add_argument("--input-json")
    finalize_input.add_argument("--input-file", type=Path)
    finalize_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    create = _internal_command(sub, "create", "Create a PRD package workspace.")
    create.add_argument("name")
    create.add_argument("--title")
    create.add_argument("--source-type", choices=["new", "legacy-brainstorm", "ad-hoc"], default="new")
    create.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    validate = _public_command(sub, "validate", help="Validate one or all packages.")
    target = validate.add_mutually_exclusive_group(required=True)
    target.add_argument("name", nargs="?")
    target.add_argument("--all", action="store_true")
    validate.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    doctor_parser = _public_command(sub, "doctor", help="Check .arbor package health and the next action. Wiki health lives in sdd-wiki lint.")
    doctor_parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings or blocked packages exist.")
    doctor_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    set_status = _public_command(sub, "set-status", help="Update package state.")
    set_status.add_argument("name")
    set_status.add_argument("--state", required=True)
    set_status.add_argument("--actor", required=True)
    set_status.add_argument("--note", default="")

    record_impl = _public_command(sub, "record-impl-result", help="Record structured package implementation result evidence.")
    record_impl.add_argument("name")
    record_impl.add_argument("--state", required=True)
    record_impl.add_argument("--summary", required=True)
    record_impl.add_argument("--acceptance", action="append", default=[])
    record_impl.add_argument("--command", dest="commands", action="append", default=[], help="Legacy note only; use --check for verification evidence.")
    record_impl.add_argument("--check", dest="checks", action="append", default=[], help="Check evidence id produced by run-check or record-check.")
    record_impl.add_argument("--functional-check", dest="functional_checks", action="append", default=[], help="Package-level functional verification check id recorded with --kind functional.")
    record_impl.add_argument("--concern", action="append", default=[])
    record_impl.add_argument("--actor", default="impl")
    record_impl.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    derive_checks_parser = _public_command(sub, "derive-required-checks", help="Derive required verification checks from slice task files.")
    derive_checks_parser.add_argument("name")
    derive_checks_parser.add_argument("--actor", default="impl")
    derive_checks_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    run_check_parser = _public_command(sub, "run-check", help="Run a verification command and record check evidence.")
    run_check_parser.add_argument("name")
    run_check_parser.add_argument("--required-check")
    run_check_parser.add_argument("--kind")
    run_check_parser.add_argument("--slice", dest="slice_id")
    run_check_parser.add_argument("--cwd", default=".")
    run_check_parser.add_argument("--timeout", type=int, default=120)
    run_check_parser.add_argument("--actor", default="impl")
    run_check_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    record_check_parser = _public_command(sub, "record-check", help="Record manual, blocked, or externally observed check evidence.")
    record_check_parser.add_argument("name")
    record_check_parser.add_argument("--required-check")
    record_check_parser.add_argument("--kind")
    record_check_parser.add_argument("--slice", dest="slice_id")
    record_check_parser.add_argument("--status", required=True, choices=sorted(CHECK_STATUSES))
    record_check_parser.add_argument("--summary", default="")
    record_check_parser.add_argument("--evidence", action="append", default=[])
    record_check_parser.add_argument("--reason", default="")
    record_check_parser.add_argument("--command", dest="check_command")
    record_check_parser.add_argument("--exit-code", type=int)
    record_check_parser.add_argument("--actor", default="impl")
    record_check_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    impl_packet_parser = _public_command(sub, "impl-packet", help="Emit a deterministic execution packet for impl (entry packet, or one slice with --slice). First use derives and persists required_checks into task.json.")
    impl_packet_parser.add_argument("name")
    impl_packet_parser.add_argument("--slice", dest="slice_id", help="Slice id (e.g. S-003) for a per-slice packet; omit for the entry packet.")
    impl_packet_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    mark_slice_parser = _public_command(sub, "mark-slice", help="Update slice progress in task.json; done is gated on check + acceptance evidence.")
    mark_slice_parser.add_argument("name")
    mark_slice_parser.add_argument("--id", required=True, help="Slice id (e.g. S-001).")
    mark_slice_parser.add_argument("--status", required=True, choices=sorted(SLICE_STATUSES), help="Slice status.")
    mark_slice_parser.add_argument("--acceptance", action="append", default=[], help='Repeatable marker evidence for --status done, e.g. "S-001: GET /x 返回 2 条 + e2e 通过"; multi-marker slices need one per S-NNN.M.')
    mark_slice_parser.add_argument("--note", default="", help="Optional progress note.")
    mark_slice_parser.add_argument("--actor", default="impl")
    mark_slice_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    record_review_parser = _public_command(sub, "record-review", help="Record structured package review verdict evidence.")
    record_review_parser.add_argument("name")
    record_review_parser.add_argument("--state", required=True)
    record_review_parser.add_argument("--summary", required=True)
    record_review_parser.add_argument("--evidence", action="append", default=[])
    record_review_parser.add_argument("--note", action="append", default=[])
    record_review_parser.add_argument("--actor", default="review")
    record_review_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    add_amendment_parser = _public_command(sub, "add-amendment", help="Record a forward-only PRD amendment.")
    add_amendment_parser.add_argument("name")
    add_amendment_parser.add_argument("--id")
    add_amendment_parser.add_argument("--title", required=True)
    add_amendment_parser.add_argument("--wrong", required=True)
    add_amendment_parser.add_argument("--correct", required=True)
    add_amendment_parser.add_argument("--affects", action="append", default=[])
    add_amendment_parser.add_argument("--source", default="user")
    add_amendment_parser.add_argument("--actor", default="brainstorm")

    set_execution_parser = _internal_command(sub, "set-execution", "Record lightweight package execution metadata.")
    set_execution_parser.add_argument("name")
    set_execution_parser.add_argument("--status", choices=sorted(EXECUTION_STATUSES))
    set_execution_parser.add_argument("--base-branch")
    set_execution_parser.add_argument("--branch")
    set_execution_parser.add_argument("--upstream")
    set_execution_parser.add_argument("--worktree")
    set_execution_parser.add_argument("--worktree-created-by")
    set_execution_parser.add_argument("--actor", default="arbor")
    set_execution_parser.add_argument("--note", default="")

    set_pr_parser = _internal_command(sub, "set-pr", "Record package-level PR metadata.")
    set_pr_parser.add_argument("name")
    set_pr_parser.add_argument("--url")
    set_pr_parser.add_argument("--number", type=int)
    set_pr_parser.add_argument("--state", choices=sorted(PR_STATES))
    set_pr_parser.add_argument("--actor", default="arbor")
    set_pr_parser.add_argument("--note", default="")

    repair_context_parser = _internal_command(sub, "repair-context", "Normalize recoverable impl/review context JSONL schema drift.")
    repair_context_parser.add_argument("name")
    repair_context_parser.add_argument("--type", required=True, choices=["impl", "review"])
    repair_context_parser.add_argument("--actor", default="arbor")
    repair_context_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    add_ctx = _public_command(sub, "add-context", help="Append one or more context JSONL entries atomically.")
    add_ctx.add_argument("name")
    add_ctx.add_argument("--type", required=True, choices=sorted(CONTEXT_TYPES))
    add_ctx.add_argument("--entry-json", action="append", default=[], help='Repeatable JSON entry, e.g. \'{"kind":"note","summary":"..."}\'.')
    add_ctx.add_argument("--entries-json", help="JSON array of entries.")
    add_ctx.add_argument("--actor", default="arbor")
    add_ctx.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    module_summary_parser = _public_command(sub, "module-summary", help="Emit a deterministic module summary packet for wiki publishing.")
    module_summary_parser.add_argument("name")
    module_summary_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    list_parser = _public_command(sub, "list", help="List packages.")
    list_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    show = _public_command(sub, "show", help="Show one package.")
    show.add_argument("name")
    show.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    return parser
