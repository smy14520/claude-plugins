"""argparse front-end: owns printing, exit codes, and store I/O wiring."""

from __future__ import annotations

import argparse
import json
import sys

from . import core, store

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tdo", description="Local CLI todo with tag filtering."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add", help="add a task")
    p.add_argument("title", metavar="TITLE")
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="TAG",
        help="tag(s); comma inside one flag splits into multiple tags",
    )

    p = sub.add_parser("ls", help="list pending tasks (use --all to include done)")
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="TAG",
        help="repeat to AND; comma inside one flag to OR",
    )
    p.add_argument("--all", action="store_true", help="include done tasks")
    p.add_argument("--json", action="store_true", help="print a JSON array of tasks")

    for name, helptext in (
        ("done", "mark a task done"),
        ("reopen", "move a done task back to pending"),
        ("rm", "delete a task (the .bak file keeps the previous state)"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("id", type=int, metavar="ID")

    p = sub.add_parser("tags", help="list tags with task counts, count desc")
    p.add_argument(
        "--json", action="store_true", help="print a JSON array of {tag, count}"
    )

    return parser


def print_rows(tasks: list[dict]) -> None:
    width = len(str(max(task["id"] for task in tasks)))
    for task in tasks:
        mark = "x" if task["status"] == core.DONE else " "
        tags = "".join(f" #{tag}" for tag in task["tags"])
        print(f"[{mark}] {task['id']:>{width}} {task['title']}{tags}")


def dispatch(args: argparse.Namespace) -> int:
    data = store.load()
    tasks = data["tasks"]

    if args.command == "add":
        tags = [tag for group in core.parse_tag_groups(args.tag) for tag in group]
        task = core.add(tasks, args.title, tags, core.take_next_id(data))
        store.save(data)
        print(f"Added #{task['id']} {task['title']}")
        return EXIT_OK

    if args.command == "ls":
        groups = core.parse_tag_groups(args.tag)
        matched, unknown = core.filter_tasks(tasks, groups, include_done=args.all)
        if unknown:
            print(f"note: no tasks use tag(s): {', '.join(unknown)}", file=sys.stderr)
        if args.json:
            print(json.dumps(matched, ensure_ascii=False, indent=2))
        elif matched:
            print_rows(matched)
        else:
            print("No matching tasks." if groups else "No tasks.")
        return EXIT_OK

    if args.command in ("done", "reopen"):
        marking_done = args.command == "done"
        task, changed = (core.done if marking_done else core.reopen)(tasks, args.id)
        if changed:
            store.save(data)
            print(f"{'Done' if marking_done else 'Reopened'} {task['id']}")
        else:
            state = "already done" if marking_done else "already pending"
            print(f"Task {task['id']} {state} (no change)")
        return EXIT_OK

    if args.command == "rm":
        task = core.remove(tasks, args.id)
        store.save(data)
        print(f"Removed {task['id']} {task['title']}")
        return EXIT_OK

    rows = core.tag_counts(tasks)  # args.command == "tags"
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif rows:
        for row in rows:
            print(f"{row['tag']} ({row['count']})")
    else:
        print("No tags.")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except (core.ValidationError, core.NotFound, store.StoreError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE if isinstance(exc, core.ValidationError) else EXIT_ERROR


def entry() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entry()
