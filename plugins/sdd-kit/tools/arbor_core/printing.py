from __future__ import annotations

from typing import Any


def print_human_list(items: list[dict[str, Any]]) -> None:
    if not items:
        print("未找到 task package。")
        return
    for item in items:
        next_action = item.get("next_action") or {}
        print(
            f"{item['name']}\tstate={item.get('state')}\tphase={item.get('current_phase')}\tsizing={item.get('package_sizing')}\t"
            f"active={item.get('active_task')}\tnext={next_action.get('skill')}:{next_action.get('task_id')}\t"
            f"exec={item.get('execution_status')} branch={item.get('branch')} pr={item.get('pr')}\t"
            f"tasks={item.get('task_count')} ready={item.get('ready_count')} blocked={item.get('blocked_count')}"
        )


def print_human_show(data: dict[str, Any]) -> None:
    print(f"Package: {data['name']}")
    print(f"路径: {data['package']}")
    print(f"状态: {data.get('state')}")
    print(f"阶段: {data.get('current_phase')}")
    print(f"当前 task: {data.get('active_task')}")
    print(f"下一步: {data.get('next_action')}")
    print(f"Package sizing: {data.get('package_sizing')}")
    print(f"Execution: {data.get('execution')}")
    print(f"PRD: {data.get('prd')}")
    print(f"Validation: {'ok' if data['validation']['ok'] else 'failed'}")
    for error in data["validation"]["errors"]:
        print(f"  - {error}")
    if data.get("tasks"):
        print("Tasks:")
        for task in data["tasks"]:
            print(f"  - {task.get('id')} {task.get('state')} {task.get('title')}")


def print_human_map_check(data: dict[str, Any]) -> None:
    print(f"Initiative: {data['initiative']}")
    print(f"Map: {data['map']}")
    labels = {
        "ready": "可推进",
        "active": "执行中",
        "blocked": "阻塞",
        "missing": "缺失",
        "complete": "完成",
    }
    for label in ["ready", "active", "blocked", "missing", "complete"]:
        print(f"{labels[label]}:")
        items = data.get(label, [])
        if not items:
            print("  - 无")
            continue
        for item in items:
            next_action = item.get("next_action") if isinstance(item.get("next_action"), dict) else {}
            detail = item.get("reason") or next_action.get("skill") or item.get("state")
            print(f"  - {item.get('name')} wave={item.get('wave')} state={item.get('state')} exec={item.get('execution_status')} detail={detail}")
            for blocker in item.get("blocked_by", []) if isinstance(item.get("blocked_by"), list) else []:
                print(f"      blocked_by {blocker.get('name')} state={blocker.get('state')} exec={blocker.get('execution_status')}")
