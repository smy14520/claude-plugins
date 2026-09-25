"""CLI 端到端接缝：argv 进、stdout/exit code 出。"""

import argparse
import sys

from .service import TaskNotFound, TodoService
from .storage import StorageError, TodoStore


def _format_tags_bracketed(tags: list[str]) -> str:
    return f" [{', '.join(tags)}]" if tags else ""


def _format_task_line(task) -> str:
    mark = "x" if task.done else " "
    tags_part = f"  {' '.join(f'#{tag}' for tag in task.tags)}" if task.tags else ""
    return f"[{mark}] {task.id}  {task.text}{tags_part}"


def _print_task_list(tasks) -> None:
    if not tasks:
        print("No tasks.")
        return
    for task in tasks:
        print(_format_task_line(task))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="本地 CLI 待办工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增任务")
    p_add.add_argument("text")
    p_add.add_argument("-t", "--tag", action="append", default=[], dest="tags", help="标签，可重复")

    p_list = sub.add_parser("list", help="列出任务（默认仅未完成）")
    p_list.add_argument("-t", "--tag", action="append", default=[], dest="tags", help="标签过滤，多值 AND")
    p_list.add_argument("--all", action="store_true", help="包含已完成任务")

    p_done = sub.add_parser("done", help="标记完成")
    p_done.add_argument("id", type=int)

    p_rm = sub.add_parser("rm", help="删除任务")
    p_rm.add_argument("id", type=int)

    sub.add_parser("tags", help="列出标签计数（全量口径）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = TodoService(TodoStore())
    try:
        if args.command == "add":
            task = service.add(args.text, args.tags)
            print(f"Added {task.id}: {task.text}{_format_tags_bracketed(task.tags)}")
        elif args.command == "list":
            _print_task_list(service.list_tasks(args.tags, include_done=args.all))
        elif args.command == "done":
            task = service.complete(args.id)
            print(f"Completed {task.id}: {task.text}")
        elif args.command == "rm":
            task = service.remove(args.id)
            print(f"Removed {task.id}: {task.text}")
        elif args.command == "tags":
            counts = sorted(service.tag_counts().items(), key=lambda kv: (-kv[1], kv[0]))
            for tag, count in counts:
                print(f"{tag} ({count})")
    except (TaskNotFound, StorageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
