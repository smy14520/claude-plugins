"""领域逻辑（Seam 2）：+tag 解析、优先级校验、交集过滤、排序。

纯函数模块，零 I/O、零存储感知：所有函数只对入参 todo 列表做变换，
使 CLI 层与测试层可以完全脱离文件系统观测行为。
"""

from __future__ import annotations

from datetime import datetime, timezone

#: 优先级唯一合法取值（单一事实来源，CLI 的 argparse choices 也引用它）
PRIORITIES = ("high", "med", "low")

_PRIORITY_RANK = {level: rank for rank, level in enumerate(PRIORITIES)}


def parse_text(raw: str) -> tuple[str, list[str]]:
    """拆分正文与内联标签。

    任何以 ``+`` 开头且其后非空的 token 一律收为标签（含未预定义的标签），
    其余 token 以单空格连回正文；标签去重并排序，保证落盘形态确定。
    """
    words: list[str] = []
    tags: set[str] = set()
    for token in raw.split():
        if token.startswith("+") and len(token) > 1:
            tags.add(token[1:])
        else:
            words.append(token)
    return " ".join(words), sorted(tags)


def validate_priority(value) -> str:
    """校验优先级；仅接受 high|med|low，非法值抛 ValueError。"""
    if value not in PRIORITIES:
        allowed = "|".join(PRIORITIES)
        raise ValueError(f"priority 仅接受 {allowed}，收到: {value!r}")
    return value


def next_id(todos: list[dict]) -> int:
    """持久化稳定 id：新增时取 max(id)+1，空表起始 1。"""
    return max((t.get("id", 0) for t in todos), default=0) + 1


def new_todo(todos: list[dict], text: str, tags: list[str], priority: str) -> dict:
    """构造一条新 todo（done=False，created_at 为 UTC ISO 时间戳）。"""
    return {
        "id": next_id(todos),
        "text": text,
        "tags": list(tags),
        "priority": priority,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def filter_todos(
    todos: list[dict], tags: "list[str] | tuple" = (), show_done: bool = False
) -> list[dict]:
    """按契约过滤并排序。

    - 多标签为交集（必须同时含全部所给标签）；
    - 默认隐藏已完成，show_done=True 时包含；
    - 排序 = 优先级（high>med>low）→ id 升序。
    """
    wanted = list(tags)
    picked = [
        t
        for t in todos
        if (show_done or not t.get("done")) and _has_all_tags(t, wanted)
    ]
    return sorted(picked, key=_sort_key)


def _has_all_tags(todo: dict, wanted: list[str]) -> bool:
    have = set(todo.get("tags", []))
    return all(tag in have for tag in wanted)


def _sort_key(todo: dict):
    rank = _PRIORITY_RANK.get(todo.get("priority", "med"), len(PRIORITIES))
    return (rank, todo.get("id", 0))
