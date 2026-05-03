from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .brainstorm_finalize import finalize_brainstorm
from .doctor import doctor
from .errors import ArborError
from .fs import now_iso
from .package_state import *
from .printing import *
from .schema import *
from .validation import validate_package
from .wiki_state import *


PUBLIC_COMMANDS = (
    "finalize-brainstorm",
    "validate",
    "doctor",
    "set-status",
    "record-impl-result",
    "record-review",
    "add-amendment",
    "set-execution",
    "set-pr",
    "add-context",
    "add-context-batch",
    "module-summary",
    "wiki-index",
    "wiki-search",
    "wiki-collect",
    "wiki-lint",
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

    doctor_parser = _public_command(sub, "doctor", help="Check project Arbor/wiki workflow health.")
    doctor_parser.add_argument("--wiki-root", default=".wiki")
    doctor_parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings or blocked packages exist.")
    doctor_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    set_status = _public_command(sub, "set-status", help="Update package state.")
    set_status.add_argument("name")
    set_status.add_argument("--state", required=True)
    set_status.add_argument("--actor", required=True)
    set_status.add_argument("--note", default="")

    set_phase = _internal_command(sub, "set-phase", "Update current phase.")
    set_phase.add_argument("name")
    set_phase.add_argument("--phase", required=True)
    set_phase.add_argument("--actor", required=True)
    set_phase.add_argument("--note", default="")

    record_impl = _public_command(sub, "record-impl-result", help="Record structured package implementation result evidence.")
    record_impl.add_argument("name")
    record_impl.add_argument("--state", required=True)
    record_impl.add_argument("--summary", required=True)
    record_impl.add_argument("--acceptance", action="append", default=[])
    record_impl.add_argument("--command", dest="commands", action="append", default=[])
    record_impl.add_argument("--concern", action="append", default=[])
    record_impl.add_argument("--actor", default="impl")
    record_impl.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    record_review_parser = _public_command(sub, "record-review", help="Record structured package review verdict evidence.")
    record_review_parser.add_argument("name")
    record_review_parser.add_argument("--state", required=True)
    record_review_parser.add_argument("--summary", required=True)
    record_review_parser.add_argument("--evidence", action="append", default=[])
    record_review_parser.add_argument("--note", action="append", default=[])
    record_review_parser.add_argument("--actor", default="review")
    record_review_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    set_prd = _internal_command(sub, "set-prd-status", "Update PRD readiness status.")
    set_prd.add_argument("name")
    set_prd.add_argument("--status", required=True, choices=["draft", "ready", "revising", "superseded"])
    set_prd.add_argument("--actor", required=True)
    set_prd.add_argument("--note", default="")

    add_amendment_parser = _public_command(sub, "add-amendment", help="Record a forward-only PRD amendment.")
    add_amendment_parser.add_argument("name")
    add_amendment_parser.add_argument("--id")
    add_amendment_parser.add_argument("--title", required=True)
    add_amendment_parser.add_argument("--wrong", required=True)
    add_amendment_parser.add_argument("--correct", required=True)
    add_amendment_parser.add_argument("--affects", action="append", default=[])
    add_amendment_parser.add_argument("--source", default="user")
    add_amendment_parser.add_argument("--actor", default="brainstorm")

    set_sizing = _internal_command(sub, "set-package-sizing", "Record package boundary sizing from brainstorm.")
    set_sizing.add_argument("name")
    set_sizing.add_argument("--status", required=True, choices=sorted(PACKAGE_SIZING_STATUSES))
    set_sizing.add_argument("--decision")
    set_sizing.add_argument("--signal", action="append", default=[])
    set_sizing.add_argument("--recommended-package", action="append", default=[], help="name[:reason]")
    set_sizing.add_argument("--phase", choices=sorted(PHASES), help="Lifecycle phase that made the boundary decision; inferred from actor when omitted.")
    set_sizing.add_argument("--actor", required=True)
    set_sizing.add_argument("--note", default="")

    set_execution_parser = _public_command(sub, "set-execution", help="Record lightweight package execution metadata.")
    set_execution_parser.add_argument("name")
    set_execution_parser.add_argument("--status", choices=sorted(EXECUTION_STATUSES))
    set_execution_parser.add_argument("--base-branch")
    set_execution_parser.add_argument("--branch")
    set_execution_parser.add_argument("--upstream")
    set_execution_parser.add_argument("--worktree")
    set_execution_parser.add_argument("--worktree-created-by")
    set_execution_parser.add_argument("--actor", default="arbor")
    set_execution_parser.add_argument("--note", default="")

    set_pr_parser = _public_command(sub, "set-pr", help="Record package-level PR metadata.")
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

    add_ctx = _public_command(sub, "add-context", help="Append context JSONL.")
    add_ctx.add_argument("name")
    add_ctx.add_argument("--type", required=True, choices=sorted(CONTEXT_TYPES))
    add_ctx.add_argument("--kind", choices=sorted(CONTEXT_KINDS))
    add_ctx.add_argument("--source")
    add_ctx.add_argument("--summary")
    add_ctx.add_argument("--actor", default="arbor")
    add_ctx.add_argument("--source-id")
    add_ctx.add_argument("--source-type", choices=sorted(SOURCE_TYPES))
    add_ctx.add_argument("--location")
    add_ctx.add_argument("--title")
    add_ctx.add_argument("--why")

    add_ctx_batch = _public_command(sub, "add-context-batch", help="Atomically append multiple context JSONL entries.")
    add_ctx_batch.add_argument("name")
    add_ctx_batch.add_argument("--type", required=True, choices=sorted(CONTEXT_TYPES))
    add_ctx_batch.add_argument("--entry-json", action="append", default=[])
    add_ctx_batch.add_argument("--entries-json")
    add_ctx_batch.add_argument("--actor", default="arbor")
    add_ctx_batch.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    module_summary_parser = _public_command(sub, "module-summary", help="Emit a deterministic module summary packet for wiki publishing.")
    module_summary_parser.add_argument("name")
    module_summary_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    wiki_index_parser = _public_command(sub, "wiki-index", help="Index project-local .wiki markdown pages.")
    wiki_index_parser.add_argument("--wiki-root", default=".wiki")
    wiki_index_parser.add_argument("--tag")
    wiki_index_parser.add_argument("--include-content", choices=["true", "false"], default="false")
    wiki_index_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    wiki_search_parser = _public_command(sub, "wiki-search", help="Search project-local .wiki pages with deterministic token scoring.")
    wiki_search_parser.add_argument("query")
    wiki_search_parser.add_argument("--wiki-root", default=".wiki")
    wiki_search_parser.add_argument("--limit", type=int)
    wiki_search_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    wiki_collect_parser = _public_command(sub, "wiki-collect", help="Collect compact summaries for relevant .wiki pages.")
    wiki_collect_parser.add_argument("--query", required=True)
    wiki_collect_parser.add_argument("--wiki-root", default=".wiki")
    wiki_collect_parser.add_argument("--limit", type=int, default=5)
    wiki_collect_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    wiki_lint_parser = _public_command(sub, "wiki-lint", help="Lint project-local .wiki markdown pages without modifying them.")
    wiki_lint_parser.add_argument("--wiki-root", default=".wiki")
    wiki_lint_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    list_parser = _public_command(sub, "list", help="List packages.")
    list_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    show = _public_command(sub, "show", help="Show one package.")
    show.add_argument("name")
    show.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    timestamp = now_iso(args.now)
    json_output = getattr(args, "json_output", False) or args.json
    try:
        if args.command == "finalize-brainstorm":
            try:
                if args.input_file:
                    spec = json.loads(args.input_file.read_text(encoding="utf-8"))
                else:
                    spec = json.loads(args.input_json)
            except json.JSONDecodeError as exc:
                raise ArborError(f"Invalid finalize-brainstorm JSON: {exc}") from exc
            result = finalize_brainstorm(root, spec, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                package_names = ", ".join(item["name"] for item in result["packages"])
                print(f"finalized: {result['root_package']} ({result['kind']})")
                print(f"packages: {package_names}")
            return 0

        if args.command == "create":
            result = create_package(root, args.name, args.title, args.source_type, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Package: {result['package']}")
                if result["created"]:
                    print("Created: " + ", ".join(result["created"]))
                else:
                    print("Package already existed; no files overwritten.")
            return 0

        if args.command == "validate":
            targets = [item["name"] for item in list_packages(root)] if args.all else [args.name]
            all_errors: dict[str, list[str]] = {}
            for name in targets:
                errors = validate_package(root, name)
                if errors:
                    all_errors[name] = errors
            if json_output:
                print(json.dumps({"ok": not all_errors, "errors": all_errors}, ensure_ascii=False, indent=2))
            elif all_errors:
                for name, errors in all_errors.items():
                    print(f"{name}: failed")
                    for error in errors:
                        print(f"  - {error}")
            else:
                print("ok")
            return 1 if all_errors else 0

        if args.command == "doctor":
            result = doctor(root, args.wiki_root, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_doctor(result)
            if not result["ok"]:
                return 1
            summary = result.get("summary", {}) if isinstance(result.get("summary"), dict) else {}
            if args.strict and (summary.get("warning_count", 0) or summary.get("blocked_count", 0)):
                return 1
            return 0

        if args.command == "set-status":
            update_package_status(root, args.name, args.state, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "set-phase":
            update_phase(root, args.name, args.phase, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "record-impl-result":
            result = record_impl_result(root, args.name, args.state, args.summary, args.acceptance, args.commands, args.concern, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("ok")
            return 0

        if args.command == "record-review":
            result = record_review(root, args.name, args.state, args.summary, args.evidence, args.note, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("ok")
            return 0

        if args.command == "set-prd-status":
            update_prd_status(root, args.name, args.status, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "add-amendment":
            add_amendment(root, args.name, args.id, args.title, args.wrong, args.correct, args.affects, args.source, args.actor, timestamp)
            print("ok")
            return 0

        if args.command == "set-package-sizing":
            set_package_sizing(root, args.name, args.status, args.actor, args.note, timestamp, args.decision, args.signal, args.recommended_package, args.phase)
            print("ok")
            return 0

        if args.command == "set-execution":
            set_execution(root, args.name, args.status, args.actor, args.note, timestamp, args.base_branch, args.branch, args.upstream, args.worktree, args.worktree_created_by)
            print("ok")
            return 0

        if args.command == "set-pr":
            set_pr(root, args.name, args.actor, args.note, timestamp, args.url, args.number, args.state)
            print("ok")
            return 0

        if args.command == "repair-context":
            result = repair_context_jsonl(root, args.name, args.type, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"repaired: {result['count']}")
            return 0

        if args.command == "add-context":
            add_context(
                root,
                args.name,
                args.type,
                args.kind,
                args.summary,
                args.source,
                args.actor,
                timestamp,
                args.source_id,
                args.source_type,
                args.location,
                args.title,
                args.why,
            )
            print("ok")
            return 0

        if args.command == "add-context-batch":
            entries = [parse_entry_json(raw) for raw in args.entry_json]
            if args.entries_json is not None:
                entries.extend(parse_entries_json(args.entries_json))
            result = add_context_batch(root, args.name, args.type, entries, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"appended: {result['count']}")
            return 0

        if args.command == "module-summary":
            result = module_summary(root, args.name, timestamp=timestamp)
            print(json.dumps(result, ensure_ascii=False, indent=2) if json_output else result["title"])
            return 0

        if args.command == "wiki-index":
            result = wiki_index(root, args.wiki_root, args.tag, args.include_content == "true")
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"pages: {len(result['pages'])}")
            return 0

        if args.command == "wiki-search":
            result = wiki_search(root, args.query, args.wiki_root, args.limit)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for item in result["results"]:
                    print(f"{item['score']} {item['path']} — {item['title']}")
            return 0

        if args.command == "wiki-collect":
            result = wiki_collect(root, args.query, args.wiki_root, args.limit)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for item in result["selected"]:
                    print(f"{item['path']} — {item['title']}")
            return 0

        if args.command == "wiki-lint":
            result = wiki_lint(root, args.wiki_root)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_wiki_lint(result)
            return 0 if result["ok"] else 1

        if args.command == "list":
            items = list_packages(root)
            if json_output:
                print(json.dumps(items, ensure_ascii=False, indent=2))
            else:
                print_human_list(items)
            return 0

        if args.command == "show":
            result = show_package(root, args.name)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_show(result)
            return 0

        parser.error(f"Unhandled command {args.command}")
        return 2
    except ArborError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
