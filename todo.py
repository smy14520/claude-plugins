#!/usr/bin/env python3
"""命令行 todo 工具 — 支持添加、完成、列表、删除任务。

数据存储在 ~/.todo/tasks.json。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".todo"
DATA_FILE = DATA_DIR / "tasks.json"


def load_tasks():
    """读取任务列表。文件不存在返回空列表，JSON 损坏报错退出。"""
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data.get("tasks", [])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"错误：tasks.json 格式损坏，无法解析 ({e})", file=sys.stderr)
        sys.exit(1)


def save_tasks(tasks):
    """写入任务列表，自动创建目录。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cmd_add(args):
    description = args.description
    if not description.strip():
        print("错误：任务描述不能为空", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {
        "id": new_id,
        "description": description,
        "done": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task #{new_id}: {description}")


def cmd_list(args):
    tasks = load_tasks()
    if not tasks:
        print("没有任务")
        return
    for task in sorted(tasks, key=lambda t: t["id"]):
        mark = "✓" if task["done"] else " "
        print(f"[{mark}] #{task['id']} {task['description']}")


def cmd_done(args):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == args.id:
            task["done"] = True
            save_tasks(tasks)
            print(f"Completed task #{task['id']}: {task['description']}")
            return
    print(f"错误：任务 #{args.id} 不存在", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task["id"] == args.id:
            removed = tasks.pop(i)
            save_tasks(tasks)
            print(f"Deleted task #{removed['id']}: {removed['description']}")
            return
    print(f"错误：任务 #{args.id} 不存在", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="命令行 todo 工具")
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser("add", help="添加任务")
    p_add.add_argument("description", help="任务描述")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = subparsers.add_parser("list", help="列出所有任务")
    p_list.set_defaults(func=cmd_list)

    # done
    p_done = subparsers.add_parser("done", help="标记任务完成")
    p_done.add_argument("id", type=int, help="任务 ID")
    p_done.set_defaults(func=cmd_done)

    # delete
    p_delete = subparsers.add_parser("delete", help="删除任务")
    p_delete.add_argument("id", type=int, help="任务 ID")
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
