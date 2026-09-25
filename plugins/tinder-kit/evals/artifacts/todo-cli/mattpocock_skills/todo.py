#!/usr/bin/env python3
"""todo — 单机单用户的极简 CLI 待办工具。

领域语言见 CONTEXT.md，存储决策见 docs/adr/0001-single-json-file-storage.md。
数据模型：Task = id / text / tags / priority / done（无时间戳）。
存储：单个本地 JSON 文件，默认 ~/.todos.json，可用环境变量 TODO_FILE 覆盖。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

PRIORITIES = ("high", "med", "low")
DEFAULT_PRIORITY = "med"
DEFAULT_FILE = Path.home() / ".todos.json"


class TodoError(Exception):
    """可预期的用户错误：消息直接展示，进程以退出码 1 结束。"""


@dataclass
class Task:
    id: int
    text: str
    tags: list[str] = field(default_factory=list)
    priority: str = DEFAULT_PRIORITY
    done: bool = False

    @classmethod
    def from_dict(cls, raw: dict) -> Task:
        # 防御式读取：手工编辑过的、字段残缺的旧文件不应让程序崩溃。
        return cls(
            id=int(raw["id"]),
            text=str(raw["text"]),
            tags=[str(tag) for tag in raw.get("tags", [])],
            priority=str(raw.get("priority") or DEFAULT_PRIORITY),
            done=bool(raw.get("done", False)),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "tags": self.tags,
            "priority": self.priority,
            "done": self.done,
        }


class Store:
    """单个 JSON 文件的读写。写走临时文件 + 原子替换。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> tuple[list[Task], int]:
        if not self.path.exists():
            return [], 1
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TodoError(f"{self.path} 不是合法 JSON，拒绝读写（{exc}）") from exc
        tasks = [Task.from_dict(item) for item in raw.get("tasks", [])]
        next_id = raw.get("next_id")
        if not isinstance(next_id, int):
            next_id = max((task.id for task in tasks), default=0) + 1
        return tasks, next_id

    def save(self, tasks: list[Task], next_id: int) -> None:
        payload = {"next_id": next_id, "tasks": [task.to_dict() for task in tasks]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".todos-", suffix=".tmp")
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(tmp_path, self.path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


def normalize_tags(tags: list[str]) -> list[str]:
    """清洗标签：strip、拒绝空串、同任务内大小写不敏感去重（保留首个输入的大小写）。"""
    cleaned: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        stripped = tag.strip()
        if not stripped:
            raise TodoError("标签不能为空")
        key = stripped.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(stripped)
    return cleaned


def parse_priority(value: str) -> str:
    lowered = value.strip().lower()
    if lowered not in PRIORITIES:
        raise argparse.ArgumentTypeError(
            f"优先级必须是 {'/'.join(PRIORITIES)} 之一，收到 {value!r}"
        )
    return lowered


def find(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise TodoError(f"不存在 ID 为 {task_id} 的任务（用 list 查看当前 ID）")


def select(
    tasks: list[Task], *, show: str, tags: list[str], priority: str | None
) -> list[Task]:
    """按可见性、优先级、标签过滤。多标签 AND、大小写不敏感，结果按 ID 升序（创建顺序）。"""
    selected = []
    for task in sorted(tasks, key=lambda t: t.id):
        if show == "open" and task.done:
            continue
        if show == "done" and not task.done:
            continue
        if priority is not None and task.priority != priority:
            continue
        lowered = {tag.lower() for tag in task.tags}
        if any(tag.lower() not in lowered for tag in tags):
            continue
        selected.append(task)
    return selected


def render(task: Task) -> str:
    checkbox = "x" if task.done else " "
    parts = [f"[{checkbox}] {task.id} {task.text}", *(f"#{tag}" for tag in task.tags)]
    if task.priority != DEFAULT_PRIORITY:
        parts.append(f"!{task.priority}")
    return " ".join(parts)


# ---- 命令实现。返回 (tasks, next_id, 是否写盘) -------------------------------------


def cmd_add(args: argparse.Namespace, tasks: list[Task], next_id: int):
    text = args.text.strip()
    if not text:
        raise TodoError("任务内容不能为空")
    if args.priority not in PRIORITIES:  # 直接调用时的兜底校验（CLI 路径已由 parse_priority 保证）
        raise TodoError(f"优先级必须是 {'/'.join(PRIORITIES)} 之一")
    task = Task(id=next_id, text=text, tags=normalize_tags(args.tag), priority=args.priority)
    tasks.append(task)
    print(render(task))
    return tasks, next_id + 1, True


def cmd_list(args: argparse.Namespace, tasks: list[Task], next_id: int):
    show = "all" if args.show_all else "done" if args.done else "open"
    selected = select(tasks, show=show, tags=args.tag, priority=args.priority)
    if selected:
        for task in selected:
            print(render(task))
    else:
        print("没有匹配的任务", file=sys.stderr)
    return tasks, next_id, False


def _set_done(args, tasks, next_id, done_value: bool, label: str):
    task = find(tasks, args.id)
    if task.done == done_value:
        print(f"任务 {task.id} 本就处于{label}状态")
    else:
        task.done = done_value
        print(render(task))
    return tasks, next_id, True


def cmd_done(args: argparse.Namespace, tasks: list[Task], next_id: int):
    return _set_done(args, tasks, next_id, True, "已完成")


def cmd_reopen(args: argparse.Namespace, tasks: list[Task], next_id: int):
    return _set_done(args, tasks, next_id, False, "未完成")


def cmd_delete(args: argparse.Namespace, tasks: list[Task], next_id: int):
    task = find(tasks, args.id)
    tasks.remove(task)
    print(f"已删除 {task.id} {task.text}")
    return tasks, next_id, True


HANDLERS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "reopen": cmd_reopen,
    "delete": cmd_delete,
    "rm": cmd_delete,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="单机单用户的极简 CLI 待办工具（标签过滤 + 本地 JSON 持久化）",
    )
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="新增任务")
    p_add.add_argument("text", help="任务内容")
    p_add.add_argument(
        "--tag", action="append", default=[], metavar="TAG", help="标签，可重复；同一任务内去重"
    )
    p_add.add_argument(
        "--priority",
        type=parse_priority,
        default=DEFAULT_PRIORITY,
        help=f"优先级 {'/'.join(PRIORITIES)}，默认 {DEFAULT_PRIORITY}",
    )

    p_list = sub.add_parser("list", help="列出任务（默认只显示未完成，按创建顺序）")
    p_list.add_argument("--tag", action="append", default=[], metavar="TAG", help="过滤标签，可重复，AND 语义")
    p_list.add_argument("--priority", type=parse_priority, default=None, metavar="P", help="按优先级过滤")
    visibility = p_list.add_mutually_exclusive_group()
    visibility.add_argument("--done", action="store_true", help="只看已完成")
    visibility.add_argument("--all", action="store_true", dest="show_all", help="全部")

    p_done = sub.add_parser("done", help="标记为已完成")
    p_reopen = sub.add_parser("reopen", help="恢复为未完成")
    p_delete = sub.add_parser("delete", aliases=["rm"], help="物理删除任务（别名 rm）")
    for p in (p_done, p_reopen, p_delete):
        p.add_argument("id", type=int, metavar="ID", help="任务 ID，来自 list 输出")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["list"]  # 裸敲 todo 等价于 todo list

    args = build_parser().parse_args(argv)
    path = Path(os.environ.get("TODO_FILE") or DEFAULT_FILE)

    try:
        tasks, next_id = Store(path).load()
        tasks, next_id, changed = HANDLERS[args.command](args, tasks, next_id)
    except TodoError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    if changed:
        Store(path).save(tasks, next_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
