"""纯领域操作：无 IO，全部为可独立测试的纯函数。

术语遵循 .forge/CONTEXT.md：Todo（两态 open/done）、Tag、Priority（high/med/low）。
"""

PRIORITIES = ("high", "med", "low")


def filter_by_tags(todos: list[dict], tags: list[str]) -> list[dict]:
    """AND 语义过滤：Todo 必须带有 tags 中的每一个；空条件 = 全量原序。"""
    if not tags:
        return todos
    return [t for t in todos if all(tag in t["tags"] for tag in tags)]


def next_id(todos: list[dict]) -> int:
    """自增 id：最大值 +1，不回填空洞；空清单从 1 起。"""
    return max((t["id"] for t in todos), default=0) + 1


def mark_done(todo: dict, now: str) -> dict:
    """翻到 done 并盖完成时间戳；返回新 dict，不改原对象。"""
    return {**todo, "status": "done", "completed_at": now}


def mark_open(todo: dict) -> dict:
    """翻回 open 并清掉完成时间戳；返回新 dict，不改原对象。"""
    return {**todo, "status": "open", "completed_at": None}


def parse_tags(raw: str) -> list[str]:
    """逗号分隔 → 去空白、去空段、去重、保持首次出现顺序。"""
    seen: set[str] = set()
    tags: list[str] = []
    for part in raw.split(","):
        tag = part.strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags
