"""Command line front-end: argparse parsing, rendering, exit codes.

stdout carries data only (list rows, ``--json`` payloads, one-line
confirmations); errors and "nothing to do" hints go to stderr. Domain errors
exit 1, argparse usage errors exit 2.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys

from .core import (
    TodoError,
    add_todo,
    clear_done,
    dedupe_tags,
    edit_todo,
    mark_done,
    remove,
    reopen,
    select,
)
from .store import FILE_NAME, PRIORITIES, StoreError, load, save

TAG_HELP = "tag; repeatable, comma-separated values are split apart"


def _tag_groups(raw: str) -> list[str]:
    """argparse type for --tag: comma split, whitespace trimmed, never empty.

    ``--tag "backend,"`` therefore means exactly ``--tag backend``: the trailing
    empty segment is dropped, while a value with no tag at all (``--tag ""``,
    ``--tag ","``) is a usage error rather than a silent no-op filter.
    """
    tags = [part.strip() for part in raw.split(",")]
    tags = [tag for tag in tags if tag]
    if not tags:
        raise argparse.ArgumentTypeError("tag must not be empty")
    return tags


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description=f"Project-local todo list stored in ./{FILE_NAME}.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    add_cmd = subparsers.add_parser("add", help="add a pending todo and print its id")
    add_cmd.add_argument("title", help="todo title (must not be empty)")
    add_cmd.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        metavar="TAG",
        type=_tag_groups,
        help=TAG_HELP,
    )
    add_cmd.add_argument(
        "-p", "--priority", choices=PRIORITIES, default="med", help="defaults to med"
    )
    add_cmd.set_defaults(handler=_run_add)

    list_cmd = subparsers.add_parser("list", help="list todos, pending only unless --all")
    list_cmd.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        metavar="TAG",
        type=_tag_groups,
        help=TAG_HELP,
    )
    list_cmd.add_argument("--priority", choices=PRIORITIES, help="keep only this priority")
    list_cmd.add_argument(
        "--all", action="store_true", dest="include_done", help="include completed todos"
    )
    list_cmd.add_argument(
        "--json", action="store_true", dest="as_json", help="print a JSON array instead of text"
    )
    list_cmd.set_defaults(handler=_run_list)

    for name, help_text, handler in (
        ("done", "mark a pending todo as done", _run_done),
        ("reopen", "move a done todo back to pending", _run_reopen),
        ("rm", "delete one todo by id", _run_rm),
    ):
        cmd = subparsers.add_parser(name, help=help_text)
        cmd.add_argument("id", type=int, metavar="ID", help="todo id, as shown by list")
        cmd.set_defaults(handler=handler)

    edit_cmd = subparsers.add_parser("edit", help="change fields of one todo in place")
    edit_cmd.add_argument("id", type=int, metavar="ID", help="todo id, as shown by list")
    edit_cmd.add_argument("--title", help="new title")
    edit_cmd.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        metavar="TAG",
        type=_tag_groups,
        help=TAG_HELP,
    )
    edit_cmd.add_argument("-p", "--priority", choices=PRIORITIES, help="new priority")
    edit_cmd.set_defaults(handler=_run_edit)

    clear_cmd = subparsers.add_parser("clear", help="delete every completed todo")
    clear_cmd.set_defaults(handler=_run_clear)

    return parser


def _flatten(groups: list[list[str]]) -> list[str]:
    """Merge every --tag occurrence into one deduplicated, order-kept list."""
    return dedupe_tags(tag for group in groups for tag in group)


def _run_add(args: argparse.Namespace) -> int:
    data = load()
    record = add_todo(
        data, title=args.title, tags=_flatten(args.tags), priority=args.priority
    )
    save(data)
    print(f"Added #{record['id']} {record['title']}")
    return 0


def _run_list(args: argparse.Namespace) -> int:
    data = load()
    todos = select(
        data,
        tags=_flatten(args.tags),
        priority=args.priority,
        include_done=args.include_done,
    )
    if args.as_json:
        print(json.dumps(todos, ensure_ascii=False, indent=2))
    else:
        for line in render_text(todos):
            print(line)
    return 0


def _run_done(args: argparse.Namespace) -> int:
    data = load()
    record = mark_done(data, args.id)
    save(data)
    print(f"Done #{record['id']} {record['title']}")
    return 0


def _run_reopen(args: argparse.Namespace) -> int:
    data = load()
    record = reopen(data, args.id)
    save(data)
    print(f"Reopened #{record['id']} {record['title']}")
    return 0


def _run_rm(args: argparse.Namespace) -> int:
    data = load()
    record = remove(data, args.id)
    save(data)
    print(f"Removed #{record['id']} {record['title']}")
    return 0


def _run_edit(args: argparse.Namespace) -> int:
    data = load()
    # An empty list means "--tag was never passed", i.e. keep the existing tags;
    # the --tag type rejects values that carry no tag at all, so this cannot be
    # confused with an attempt to clear tags.
    tags = _flatten(args.tags) if args.tags else None
    record, changed = edit_todo(
        data,
        args.id,
        title=args.title,
        tags=tags,
        priority=args.priority,
    )
    if changed:
        save(data)
    print(f"Updated #{record['id']} {record['title']}")
    return 0


def _run_clear(args: argparse.Namespace) -> int:
    data = load()
    removed = clear_done(data)
    if not removed:
        print("no completed todos to clear", file=sys.stderr)
        return 0
    save(data)
    print(f"Cleared {len(removed)} completed item(s)")
    return 0


def render_text(todos: list[dict]) -> list[str]:
    """One line per todo: id, completion marker, priority, tags, title."""
    lines = []
    for record in todos:
        parts = [
            f"#{record['id']}",
            "[x]" if record["done"] else "[ ]",
            record["priority"],
            *[f"@{tag}" for tag in record["tags"]],
            record["title"],
        ]
        lines.append(" ".join(parts))
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (TodoError, StoreError) as exc:
        print(f"todo: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # `todo list | head` closes the pipe early; keep the exit clean instead
        # of letting the interpreter report a failed stdout flush at shutdown.
        with contextlib.suppress(OSError):
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except OSError as exc:
        # Unwritable directory, disk full, ...: a message, not a traceback.
        print(f"todo: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
