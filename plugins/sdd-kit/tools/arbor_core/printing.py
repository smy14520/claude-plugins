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


def print_human_wiki_lint(data: dict[str, Any]) -> None:
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    print(f"Wiki: {data.get('wiki_root')}")
    print(f"Errors: {summary.get('error_count', 0)}")
    for issue in data.get("errors", []):
        print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")
    print(f"Warnings: {summary.get('warning_count', 0)}")
    for issue in data.get("warnings", []):
        print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")


def print_human_doctor(data: dict[str, Any]) -> None:
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    tasks = data.get("tasks", {}) if isinstance(data.get("tasks"), dict) else {}
    wiki = data.get("wiki", {}) if isinstance(data.get("wiki"), dict) else {}
    maps = data.get("maps", {}) if isinstance(data.get("maps"), dict) else {}
    print("Arbor doctor")
    print("")
    print(f"Tasks: {'ok' if tasks.get('ok') else 'failed'}")
    if wiki.get("skipped"):
        print(f"Wiki: skipped ({wiki.get('wiki_root')})")
    else:
        wiki_summary = wiki.get("summary", {}) if isinstance(wiki.get("summary"), dict) else {}
        wiki_status = "ok" if wiki.get("ok") else "failed"
        print(f"Wiki: {wiki_status} ({wiki_summary.get('warning_count', 0)} warnings)")
    print(f"Maps: {summary.get('blocked_count', 0)} blocked packages")

    task_errors = tasks.get("errors", {}) if isinstance(tasks.get("errors"), dict) else {}
    if task_errors:
        print("")
        print("Task errors:")
        for name, errors in task_errors.items():
            for error in errors:
                print(f"  - {name}: {error}")

    wiki_errors = wiki.get("errors", []) if isinstance(wiki.get("errors"), list) else []
    wiki_warnings = wiki.get("warnings", []) if isinstance(wiki.get("warnings"), list) else []
    if wiki_errors:
        print("")
        print("Wiki errors:")
        for issue in wiki_errors:
            print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")
    if wiki_warnings:
        print("")
        print("Wiki warnings:")
        for issue in wiki_warnings:
            print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")

    map_errors = maps.get("errors", []) if isinstance(maps.get("errors"), list) else []
    if map_errors:
        print("")
        print("Map errors:")
        for issue in map_errors:
            print(f"  - {issue.get('initiative')}: {issue.get('message')}")

    blocked_lines: list[str] = []
    for initiative in maps.get("initiatives", []) if isinstance(maps.get("initiatives"), list) else []:
        for item in initiative.get("blocked", []) if isinstance(initiative.get("blocked"), list) else []:
            blocked_lines.append(f"  - {initiative.get('initiative')}/{item.get('name')}: {item.get('reason')}")
        for item in initiative.get("missing", []) if isinstance(initiative.get("missing"), list) else []:
            blocked_lines.append(f"  - {initiative.get('initiative')}/{item.get('name')}: {item.get('reason')}")
    if blocked_lines:
        print("")
        print("Blocked:")
        for line in blocked_lines:
            print(line)

    print("")
    print("Result: " + ("ok" if data.get("ok") else "failed"))



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
            for blocker in item.get("contract_blockers", []) if isinstance(item.get("contract_blockers"), list) else []:
                print(f"      contract {blocker.get('id')} status={blocker.get('status')} producer={blocker.get('producer')}")
