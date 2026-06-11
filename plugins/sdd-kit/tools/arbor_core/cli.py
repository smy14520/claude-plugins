from __future__ import annotations

import json
import sys
from pathlib import Path

from .brainstorm_finalize import finalize_brainstorm
from .cli_parser import PUBLIC_COMMANDS, build_parser
from .doctor import doctor
from .errors import ArborError
from .fs import now_iso
from .module_summary import module_summary
from .package_packet import impl_packet
from .package_state import *
from .printing import *
from .schema import *
from .validation import validate_package


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    command_args: list[str] = []
    parse_argv = argv
    if "run-check" in argv:
        command_index = argv.index("run-check")
        tail = argv[command_index + 1:]
        if "--" in tail:
            separator_index = tail.index("--")
            command_args = tail[separator_index + 1:]
            parse_argv = argv[: command_index + 1 + separator_index]
    args = parser.parse_args(parse_argv)
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
            result = doctor(root, timestamp)
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

        if args.command == "record-impl-result":
            result = record_impl_result(root, args.name, args.state, args.summary, args.acceptance, args.commands, args.checks, args.functional_checks, args.concern, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("ok")
            return 0

        if args.command == "derive-required-checks":
            result = derive_required_checks(root, args.name, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"required checks: {len(result['required_checks'])}")
            return 0

        if args.command == "run-check":
            result = run_check(root, args.name, args.required_check, args.kind, args.slice_id, args.cwd, args.timeout, command_args, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                check = result["check"]
                print(f"{check['id']}: {check['status']}")
            return 0 if result["check"]["status"] == "passed" else 1

        if args.command == "record-check":
            result = record_check(root, args.name, args.required_check, args.kind, args.slice_id, args.status, args.summary, args.evidence, args.reason, args.check_command, args.exit_code, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                check = result["check"]
                print(f"{check['id']}: {check['status']}")
            return 0

        if args.command == "impl-packet":
            result = impl_packet(root, args.name, args.slice_id, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            elif args.slice_id:
                slice_info = result["slice"]
                print(f"{slice_info['id']} ({slice_info['status']}): {slice_info['title']}")
                print(f"task_file: {slice_info['task_file']}")
                print(f"required_checks: {', '.join(item['id'] for item in result['required_checks']) or 'none'}")
                print("read_next: " + ", ".join(result["read_next"]))
            else:
                for row in result["slices"]:
                    print(f"{row['id']} {row['status']} — {row['title']}")
                print(f"next_slice: {result['next_slice'] or 'none'}")
            return 0

        if args.command == "mark-slice":
            result = mark_slice(root, args.name, args.id, args.status, args.note, args.actor, timestamp, args.acceptance)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"{result['slice']}: {result['status']}")
                for concern in result.get("concerns", []):
                    print(f"concern: {concern}")
            return 0

        if args.command == "record-review":
            result = record_review(root, args.name, args.state, args.summary, args.evidence, args.note, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("ok")
            return 0

        if args.command == "add-amendment":
            add_amendment(root, args.name, args.id, args.title, args.wrong, args.correct, args.affects, args.source, args.actor, timestamp)
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
