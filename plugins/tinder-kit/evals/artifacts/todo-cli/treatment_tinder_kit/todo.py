#!/usr/bin/env python3
"""todo — 单文件本地 CLI 待办工具：标签过滤 + 本地持久化。

用法:
    todo add "修复登录 #work #urgent" --priority high
    todo list --tag work --priority high
    todo list --all / --done
    todo done 1
    todo rm 1            # delete 为别名

存储: 默认 ~/.todos.json（单个 JSON 文件，无任何数据库），
      可用环境变量 TODO_FILE 覆盖路径。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

PRIORITIES = ("high", "med", "low")
PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}
DEFAULT_STORE = "~/.todos.json"


class TodoError(Exception):
    """面向用户的错误：消息打印到 stderr，进程以退出码 1 结束。"""


# ---------- 存储层 ----------

def store_path() -> str:
    return os.path.expanduser(os.environ.get("TODO_FILE", DEFAULT_STORE))


def new_store() -> dict:
    return {"next_id": 1, "tasks": []}


def load_store(path: str) -> dict:
    """读取存储；文件缺失时返回空库，结构损坏时报错而非静默重置。"""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return new_store()
    except json.JSONDecodeError as exc:
        raise TodoError(f"存储文件不是有效 JSON：{path}（{exc}）") from exc
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise TodoError(f"存储文件结构损坏：{path}")
    if not isinstance(data.get("next_id"), int):
        # 兼容手工编辑过的文件：缺 next_id 时按现存最大 id 推导
        data["next_id"] = max((t.get("id", 0) for t in data["tasks"]), default=0) + 1
    return data


def save_store(path: str, data: dict) -> None:
    """原子写入：先写临时文件再替换，避免写一半损坏存储。"""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


# ---------- 领域逻辑 ----------

def parse_tags(text: str) -> tuple[str, list[str]]:
    """抽取正文中的 #tag（去重保序），返回 (去除标签的正文, tags)。"""
    words, tags = [], []
    for word in text.split():
        if len(word) > 1 and word.startswith("#"):
            tag = word.lstrip("#")
            if tag not in tags:
                tags.append(tag)
        else:
            words.append(word)
    return " ".join(words), tags


def merge_tags(*groups: list[str]) -> list[str]:
    """按序合并多组标签，去重保序。"""
    merged: list[str] = []
    for group in groups:
        for tag in group:
            if tag and tag not in merged:
                merged.append(tag)
    return merged


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def find_task(store: dict, task_id: int) -> dict:
    for task in store["tasks"]:
        if task.get("id") == task_id:
            return task
    raise TodoError(f"未找到 id={task_id}")


def matches(task: dict, tags: list[str], priority: str | None) -> bool:
    """多标签 AND；priority 与标签按 AND 组合。"""
    own = task.get("tags", [])
    if not all(tag in own for tag in tags):
        return False
    return priority is None or task.get("priority") == priority


def sort_tasks(tasks: list[dict]) -> list[dict]:
    """优先级 high→med→low 为主序，id 升序为次序。"""
    return sorted(
        tasks,
        key=lambda t: (PRIORITY_RANK.get(t.get("priority"), len(PRIORITY_RANK)), t.get("id", 0)),
    )


def format_task(task: dict) -> str:
    marker = "x" if task.get("done") else " "
    tags = "".join(f" #{tag}" for tag in task.get("tags", []))
    return f"{task.get('id', 0):>3}  [{marker}] ({task.get('priority', 'med')}) {task.get('text', '')}{tags}"


# ---------- 命令处理 ----------

def cmd_add(args: argparse.Namespace) -> int:
    path = store_path()
    store = load_store(path)
    text, inline_tags = parse_tags(" ".join(args.text))
    if not text:
        raise TodoError("正文不能为空（仅有标签不算一条待办）")
    tags = merge_tags(inline_tags, args.tag or [])
    task = {
        "id": store["next_id"],
        "text": text,
        "tags": tags,
        "priority": args.priority,
        "done": False,
        "created_at": now_iso(),
        "completed_at": None,
    }
    store["tasks"].append(task)
    store["next_id"] += 1
    save_store(path, store)
    print(f"已添加 {format_task(task)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = load_store(store_path())
    if args.done:
        tasks = [t for t in store["tasks"] if t.get("done")]
    elif args.all:
        tasks = list(store["tasks"])
    else:
        tasks = [t for t in store["tasks"] if not t.get("done")]
    tasks = [t for t in tasks if matches(t, args.tag or [], args.priority)]
    if not tasks:
        print("（无匹配待办）")
        return 0
    for task in sort_tasks(tasks):
        print(format_task(task))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    path = store_path()
    store = load_store(path)
    task = find_task(store, args.id)
    if task.get("done"):
        print(f"{args.id} 已是完成状态")
        return 0
    task["done"] = True
    task["completed_at"] = now_iso()
    save_store(path, store)
    print(f"已完成 {format_task(task)}")
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    path = store_path()
    store = load_store(path)
    task = find_task(store, args.id)
    store["tasks"].remove(task)
    save_store(path, store)
    print(f"已删除 {format_task(task)}")
    return 0


# ---------- CLI 装配 ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo", description="本地待办工具：标签过滤 + 本地持久化（单 JSON 文件）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增待办")
    p_add.add_argument("text", nargs="+", help="待办正文，可用 #tag 内联标签")
    # 注意：append 不给 default=[]，避免同一进程内多次 parse 共享可变默认值
    p_add.add_argument("-t", "--tag", action="append", help="追加标签（可重复）")
    p_add.add_argument("-p", "--priority", choices=PRIORITIES, default="med", help="优先级（默认 med）")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="列出待办（默认仅未完成）")
    p_list.add_argument("-t", "--tag", action="append", help="按标签过滤，多标签 AND（可重复）")
    p_list.add_argument("-p", "--priority", choices=PRIORITIES, help="按优先级过滤（与 --tag AND 组合）")
    p_list.add_argument("--all", action="store_true", help="显示全部（含已完成）")
    p_list.add_argument("--done", action="store_true", help="仅显示已完成")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="标记完成（幂等）")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)

    p_rm = sub.add_parser("rm", aliases=["delete"], help="删除待办（delete 为别名）")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=cmd_rm)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except TodoError as exc:
        print(f"todo: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
