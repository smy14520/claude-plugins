from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import ArborError
from .fs import now_iso
from .map_state import *
from .package_state import *
from .printing import *
from .schema import *
from .validation import validate_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage sdd-kit Arbor task packages.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root containing .arbor/.")
    parser.add_argument("--now", help="Override timestamp for deterministic tests.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for list/show/create.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a task package.")
    create.add_argument("name")
    create.add_argument("--mode", choices=sorted(MODES), default="strict-atomic")
    create.add_argument("--title")
    create.add_argument("--source-type", choices=["new", "legacy-brainstorm", "ad-hoc", "map-split"], default="new")
    create.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    create_map_parser = sub.add_parser("create-map", help="Create an initiative map workspace with map.md and map.json.")
    create_map_parser.add_argument("initiative")
    create_map_parser.add_argument("--title")
    create_map_parser.add_argument("--status", choices=["draft", "active", "ready", "closed", "superseded"], default="draft")
    create_map_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    split = sub.add_parser("create-split-packages", help="Materialize child task package stubs from an initiative map.")
    split.add_argument("initiative")
    split.add_argument("--package", action="append", required=True, help="name::title::dep1,dep2::boundary_reason")
    split.add_argument("--mode", choices=sorted(MODES), default="strict-atomic")
    split.add_argument("--decision", required=True)
    split.add_argument("--actor", default="map")
    split.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    map_check_parser = sub.add_parser("map-check", help="Check package readiness and blockers for an initiative map.")
    map_check_parser.add_argument("initiative")
    map_check_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    map_plan_agents_parser = sub.add_parser("map-plan-agents", help="Create lead-owned rolling Agent Team/worktree worker assignment/context plan.")
    map_plan_agents_parser.add_argument("initiative")
    map_plan_agents_parser.add_argument("--max-parallel", type=int, default=3)
    map_plan_agents_parser.add_argument("--actor", default="map")
    map_plan_agents_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    validate = sub.add_parser("validate", help="Validate one or all task packages.")
    target = validate.add_mutually_exclusive_group(required=True)
    target.add_argument("name", nargs="?")
    target.add_argument("--all", action="store_true")

    set_status = sub.add_parser("set-status", help="Update package or task state.")
    set_status.add_argument("name")
    set_status.add_argument("--task")
    set_status.add_argument("--state", required=True)
    set_status.add_argument("--actor", required=True)
    set_status.add_argument("--note", default="")

    set_phase = sub.add_parser("set-phase", help="Update current phase.")
    set_phase.add_argument("name")
    set_phase.add_argument("--phase", required=True)
    set_phase.add_argument("--task")
    set_phase.add_argument("--actor", required=True)
    set_phase.add_argument("--note", default="")

    set_prd = sub.add_parser("set-prd-status", help="Update PRD readiness status.")
    set_prd.add_argument("name")
    set_prd.add_argument("--status", required=True, choices=["draft", "ready-for-task", "revising", "superseded"])
    set_prd.add_argument("--actor", required=True)
    set_prd.add_argument("--note", default="")

    add_amendment_parser = sub.add_parser("add-amendment", help="Record a forward-only PRD amendment and route to task append mode.")
    add_amendment_parser.add_argument("name")
    add_amendment_parser.add_argument("--id")
    add_amendment_parser.add_argument("--title", required=True)
    add_amendment_parser.add_argument("--wrong", required=True)
    add_amendment_parser.add_argument("--correct", required=True)
    add_amendment_parser.add_argument("--affects-task", action="append", default=[])
    add_amendment_parser.add_argument("--source", default="user")
    add_amendment_parser.add_argument("--actor", default="brainstorm")

    set_sizing = sub.add_parser("set-package-sizing", help="Record package boundary sizing from brainstorm/map; task uses it as a guard.")
    set_sizing.add_argument("name")
    set_sizing.add_argument("--status", required=True, choices=sorted(PACKAGE_SIZING_STATUSES))
    set_sizing.add_argument("--decision")
    set_sizing.add_argument("--signal", action="append", default=[])
    set_sizing.add_argument("--recommended-package", action="append", default=[], help="name[:dep1,dep2[:reason]]")
    set_sizing.add_argument("--phase", choices=sorted(PHASES), help="Lifecycle phase that made the boundary decision; inferred from actor when omitted.")
    set_sizing.add_argument("--actor", required=True)
    set_sizing.add_argument("--note", default="")

    freeze = sub.add_parser("freeze-definition", help="Mark task.md as frozen and ready for implementation.")
    freeze.add_argument("name")
    freeze.add_argument("--actor", required=True)
    freeze.add_argument("--note", default="")

    claim = sub.add_parser("claim-package", help="Record a package-level execution claim.")
    claim.add_argument("name")
    claim.add_argument("--owner", required=True)
    claim.add_argument("--branch")
    claim.add_argument("--base-branch")
    claim.add_argument("--worktree")
    claim.add_argument("--session")
    claim.add_argument("--force", action="store_true")
    claim.add_argument("--actor", default="arbor")
    claim.add_argument("--note", default="")

    release = sub.add_parser("release-package", help="Release a package-level execution claim.")
    release.add_argument("name")
    release.add_argument("--owner")
    release.add_argument("--force", action="store_true")
    release.add_argument("--actor", default="arbor")
    release.add_argument("--note", default="")

    set_execution_parser = sub.add_parser("set-execution", help="Record package-level branch/worktree execution metadata.")
    set_execution_parser.add_argument("name")
    set_execution_parser.add_argument("--status", choices=sorted(EXECUTION_STATUSES))
    set_execution_parser.add_argument("--base-branch")
    set_execution_parser.add_argument("--branch")
    set_execution_parser.add_argument("--upstream")
    set_execution_parser.add_argument("--worktree")
    set_execution_parser.add_argument("--worktree-created-by")
    set_execution_parser.add_argument("--actor", default="arbor")
    set_execution_parser.add_argument("--note", default="")

    set_pr_parser = sub.add_parser("set-pr", help="Record package-level PR metadata.")
    set_pr_parser.add_argument("name")
    set_pr_parser.add_argument("--url")
    set_pr_parser.add_argument("--number", type=int)
    set_pr_parser.add_argument("--state", choices=sorted(PR_STATES))
    set_pr_parser.add_argument("--actor", default="arbor")
    set_pr_parser.add_argument("--note", default="")

    record_checkpoint_parser = sub.add_parser("record-checkpoint", help="Record a local git checkpoint used for parallel code synchronization.")
    record_checkpoint_parser.add_argument("name")
    record_checkpoint_parser.add_argument("--kind", required=True, choices=sorted(CHECKPOINT_KINDS))
    record_checkpoint_parser.add_argument("--sha", required=True)
    record_checkpoint_parser.add_argument("--branch")
    record_checkpoint_parser.add_argument("--base-sha")
    record_checkpoint_parser.add_argument("--actor", default="parallel")
    record_checkpoint_parser.add_argument("--note", default="")

    record_agent_parser = sub.add_parser("record-agent", help="Record explicit external agent validation metadata.")
    record_agent_parser.add_argument("name")
    record_agent_parser.add_argument("--role", required=True, choices=sorted(AGENT_RECORD_ROLES))
    record_agent_parser.add_argument("--agent", required=True)
    record_agent_parser.add_argument("--status", required=True, choices=sorted(AGENT_RECORD_STATUSES))
    record_agent_parser.add_argument("--task")
    record_agent_parser.add_argument("--summary", required=True)
    record_agent_parser.add_argument("--actor", default="arbor")
    record_agent_parser.add_argument("--note", default="")

    add_child_parser = sub.add_parser("add-child", help="Add a task lifecycle record.")
    add_child_parser.add_argument("name")
    add_child_parser.add_argument("--id", required=True)
    add_child_parser.add_argument("--title", required=True)
    add_child_parser.add_argument("--milestone", required=True)
    add_child_parser.add_argument("--role", required=True, choices=sorted(ROLES))
    add_child_parser.add_argument("--depends-on", default="")
    add_child_parser.add_argument("--ready", choices=["true", "false"], default="true")
    add_child_parser.add_argument("--blocker", action="append", default=[])
    add_child_parser.add_argument("--source-amendment")
    add_child_parser.add_argument("--corrects", default="")

    add_ctx = sub.add_parser("add-context", help="Append context JSONL.")
    add_ctx.add_argument("name")
    add_ctx.add_argument("--type", required=True, choices=sorted(CONTEXT_TYPES))
    add_ctx.add_argument("--task")
    add_ctx.add_argument("--kind", choices=sorted(CONTEXT_KINDS))
    add_ctx.add_argument("--source")
    add_ctx.add_argument("--summary")
    add_ctx.add_argument("--actor", default="task")
    add_ctx.add_argument("--source-id")
    add_ctx.add_argument("--source-type", choices=sorted(SOURCE_TYPES))
    add_ctx.add_argument("--location")
    add_ctx.add_argument("--title")
    add_ctx.add_argument("--why")

    list_parser = sub.add_parser("list", help="List task packages.")
    list_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    show = sub.add_parser("show", help="Show one task package.")
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
        if args.command == "create":
            result = create_package(root, args.name, args.mode, args.title, args.source_type, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Package: {result['package']}")
                if result["created"]:
                    print("Created: " + ", ".join(result["created"]))
                else:
                    print("Package already existed; no files overwritten.")
            return 0

        if args.command == "create-map":
            result = create_map(root, args.initiative, args.title, timestamp, args.status)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Initiative: {result['initiative']}")
                print(f"Map: {result['map']}")
                if result["created"]:
                    print("Created: " + ", ".join(result["created"]))
                else:
                    print("Map already existed; no files overwritten.")
            return 0

        if args.command == "create-split-packages":
            result = create_split_packages(root, args.initiative, args.package, args.actor, args.mode, args.decision, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Initiative: {result['initiative']}")
                print(f"Map: {result['map']}")
                for item in result["packages"]:
                    created = ", ".join(item["created"]) if item["created"] else "already existed"
                    print(f"  - {item['name']}: {created}")
            return 0

        if args.command == "map-check":
            result = map_check(root, args.initiative, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_map_check(result)
            return 0

        if args.command == "map-plan-agents":
            result = map_plan_agents(root, args.initiative, args.max_parallel, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_agent_plan(result)
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

        if args.command == "set-status":
            update_task_status(root, args.name, args.task, args.state, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "set-phase":
            update_phase(root, args.name, args.phase, args.actor, args.note, args.task, timestamp)
            print("ok")
            return 0

        if args.command == "set-prd-status":
            update_prd_status(root, args.name, args.status, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "add-amendment":
            add_amendment(root, args.name, args.id, args.title, args.wrong, args.correct, args.affects_task, args.source, args.actor, timestamp)
            print("ok")
            return 0

        if args.command == "set-package-sizing":
            set_package_sizing(root, args.name, args.status, args.actor, args.note, timestamp, args.decision, args.signal, args.recommended_package, args.phase)
            print("ok")
            return 0

        if args.command == "freeze-definition":
            freeze_definition(root, args.name, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "claim-package":
            claim_package(root, args.name, args.owner, args.actor, args.note, timestamp, args.force, args.branch, args.base_branch, args.worktree, args.session)
            print("ok")
            return 0

        if args.command == "release-package":
            release_package(root, args.name, args.owner, args.actor, args.note, timestamp, args.force)
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

        if args.command == "record-checkpoint":
            record_checkpoint(root, args.name, args.kind, args.sha, args.branch, args.base_sha, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "record-agent":
            record_agent(root, args.name, args.role, args.agent, args.status, args.summary, args.actor, args.note, timestamp, args.task)
            print("ok")
            return 0

        if args.command == "add-child":
            deps = [item.strip() for item in args.depends_on.split(",") if item.strip()]
            corrects = [item.strip() for item in args.corrects.split(",") if item.strip()]
            ready = args.ready == "true"
            add_child(root, args.name, args.id, args.title, args.milestone, args.role, deps, ready, args.blocker, timestamp, args.source_amendment, corrects)
            print("ok")
            return 0

        if args.command == "add-context":
            add_context(
                root,
                args.name,
                args.type,
                args.task,
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