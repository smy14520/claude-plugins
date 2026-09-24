#!/usr/bin/env python3
"""todo — 本地 CLI 待办工具。

一次性子命令（add / list / done / delete），标签过滤，
单一 JSON 文件持久化（默认 ~/.todos.json，可用 TODO_STORE 覆盖）。
零第三方依赖，Python 3.10+。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

PRIORITIES = ("high", "med", "low")
PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}


def store_path() -> Path:
    return Path(os.environ.get("TODO_STORE") or Path.home() / ".todos.json")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def die(msg: str):
    print(f"todo: 错误：{msg}", file=sys.stderr)
    raise SystemExit(1)


def load() -> dict:
    path = store_path()
    if not path.exists():
        return {"next_id": 1, "todos": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        die(f"无法读取存储文件 {path}：{exc}。为防数据丢失，已中止，不做任何写入。")
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("todos"), list)
        or not isinstance(data.get("next_id"), int)
    ):
        die(f"存储文件 {path} 结构不符合预期（需要 todos 列表 + next_id 整数）。已中止，不做任何写入。")
    return data


def save(data: dict) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # 写临时文件再原子改名，中途崩溃不会留下半个文件
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".todos-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def parse_tags(chunks: list[str] | None) -> list[str]:
    tags: list[str] = []
    for chunk in chunks or []:
        for tag in chunk.split(","):
            tag = tag.strip()
            if tag and tag not in tags:
                tags.append(tag)
    return tags


def find_todo(data: dict, todo_id: int) -> dict:
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            return todo
    die(f"找不到 #{todo_id}。可用 id 见 `todo list`。")


def dwidth(text: str) -> int:
    """终端显示宽度：全角/宽字符按 2 计。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - dwidth(text))


def cmd_add(args: argparse.Namespace) -> None:
    data = load()
    tags = parse_tags(args.tag)
    todo = {
        "id": data["next_id"],
        "title": " ".join(args.title),
        "tags": tags,
        "priority": args.priority,
        "done": False,
        "created_at": now_iso(),
        "completed_at": None,
    }
    data["todos"].append(todo)
    data["next_id"] += 1
    save(data)
    suffix = " ".join(f"#{t}" for t in tags)
    print(f"已添加 #{todo['id']} [{todo['priority']}] {todo['title']}" + (f" {suffix}" if suffix else ""))


def cmd_list(args: argparse.Namespace) -> None:
    todos = list(load()["todos"])
    if args.done:
        todos = [t for t in todos if t["done"]]
    elif not args.all:
        todos = [t for t in todos if not t["done"]]
    want_tags = parse_tags(args.tag)
    if want_tags:  # AND：每条标签都得具备
        todos = [t for t in todos if all(w in t["tags"] for w in want_tags)]
    if args.priority:
        todos = [t for t in todos if t["priority"] == args.priority]
    todos.sort(key=lambda t: (PRIORITY_RANK.get(t["priority"], 99), t.get("created_at") or ""))

    if not todos:
        print("（没有匹配的 todo）")
        return
    w_id = max(dwidth("id"), max(dwidth(str(t["id"])) for t in todos))
    w_pri = max(dwidth("优先级"), max(dwidth(t["priority"]) for t in todos))
    tag_strs = [" ".join(f"#{tag}" for tag in t["tags"]) or "-" for t in todos]
    w_tag = max(dwidth("标签"), max(dwidth(s) for s in tag_strs))
    print(f"{pad('id', w_id)}  {pad('优先级', w_pri)}  {pad('标签', w_tag)}  标题")
    for todo, tag_str in zip(todos, tag_strs):
        title = ("✓ " if todo["done"] else "") + todo["title"]
        print(f"{pad(str(todo['id']), w_id)}  {pad(todo['priority'], w_pri)}  {pad(tag_str, w_tag)}  {title}")


def cmd_done(args: argparse.Namespace) -> None:
    data = load()
    todo = find_todo(data, args.id)
    if todo["done"]:
        print(f"#{args.id} 已是完成状态（completed_at={todo['completed_at']}），未改动。")
        return
    todo["done"] = True
    todo["completed_at"] = now_iso()
    save(data)
    print(f"完成 #{todo['id']} {todo['title']}")


def cmd_delete(args: argparse.Namespace) -> None:
    data = load()
    todo = find_todo(data, args.id)
    data["todos"].remove(todo)
    save(data)
    print(f"已删除 #{todo['id']} {todo['title']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="本地 CLI 待办工具：标签过滤 + 单文件 JSON 持久化（~/.todos.json）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  todo add 买菜 -t 跑腿,生活 -p high\n"
               "  todo list -t 工作\n"
               "  todo done 1\n"
               "  todo delete 1",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="命令")

    add = sub.add_parser("add", help="新增一条 todo")
    add.add_argument("title", nargs="+", help="标题（多个词以空格连接，可不加引号）")
    add.add_argument("-t", "--tag", action="append", metavar="标签",
                     help="标签；可重复使用，也可逗号分隔（如 -t 工作,紧急）")
    add.add_argument("-p", "--priority", choices=PRIORITIES, default="med", help="优先级，缺省 med")
    add.set_defaults(func=cmd_add)

    lst = sub.add_parser("list", aliases=["ls"], help="列出 todo（默认隐藏已完成）")
    lst.add_argument("-t", "--tag", action="append", metavar="标签",
                     help="按标签过滤；多个标签为“同时满足”（AND）")
    lst.add_argument("-p", "--priority", choices=PRIORITIES, help="按优先级过滤")
    status = lst.add_mutually_exclusive_group()
    status.add_argument("-a", "--all", action="store_true", help="包含已完成")
    status.add_argument("--done", action="store_true", help="只看已完成")
    lst.set_defaults(func=cmd_list)

    done = sub.add_parser("done", help="标记完成（幂等）")
    done.add_argument("id", type=int)
    done.set_defaults(func=cmd_done)

    delete = sub.add_parser("delete", aliases=["rm"], help="删除（立即生效，不可恢复）")
    delete.add_argument("id", type=int)
    delete.set_defaults(func=cmd_delete)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
