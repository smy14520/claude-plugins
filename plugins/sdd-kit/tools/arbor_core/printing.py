from __future__ import annotations

def print_human_list(items: list[dict[str, Any]]) -> None:
    if not items:
        print("No task packages found.")
        return
    for item in items:
        next_action = item.get("next_action") or {}
        print(
            f"{item['name']}\tstate={item.get('state')}\tphase={item.get('current_phase')}\tsizing={item.get('package_sizing')}\t"
            f"active={item.get('active_task')}\tnext={next_action.get('skill')}:{next_action.get('task_id')}\t"
            f"exec={item.get('execution_status')} owner={item.get('execution_owner')} branch={item.get('branch')} pr={item.get('pr')}\t"
            f"tasks={item.get('task_count')} ready={item.get('ready_count')} blocked={item.get('blocked_count')}"
        )


def print_human_show(data: dict[str, Any]) -> None:
    print(f"Package: {data['name']}")
    print(f"Path: {data['package']}")
    print(f"State: {data.get('state')}")
    print(f"Phase: {data.get('current_phase')}")
    print(f"Active task: {data.get('active_task')}")
    print(f"Next action: {data.get('next_action')}")
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
    for label in ["execution_ready", "prep_ready", "active", "blocked", "missing", "complete"]:
        print(f"{label.replace('_', ' ').capitalize()}:")
        items = data.get(label, [])
        if not items:
            print("  - none")
            continue
        for item in items:
            detail = item.get("reason") or item.get("assignment_kind") or item.get("next_action", {}).get("skill") or item.get("state")
            limit = f" allowed_until={item.get('allowed_until')} stop_before={item.get('stop_before')}" if item.get("assignment_kind") else ""
            print(f"  - {item.get('name')} wave={item.get('wave')} state={item.get('state')} exec={item.get('execution_status')} detail={detail}{limit}")
            for blocker in item.get("blocked_by", []) if isinstance(item.get("blocked_by"), list) else []:
                print(f"      blocked_by {blocker.get('name')} state={blocker.get('state')} exec={blocker.get('execution_status')}")


def print_human_agent_plan(data: dict[str, Any]) -> None:
    print(f"Initiative: {data['initiative']}")
    print(f"Strategy: {data['strategy']} max_parallel={data['max_parallel']} lead={data.get('lead')}")
    print(f"Team runtime: {data.get('team_name')} runtime={data.get('runtime')} isolation=worktree")
    print("Mode: main-session lead + bounded rolling Agent Team worker pool; explicit stage skills are the manual review-gated path")
    if not data.get("assignments"):
        print("Assignments: none")
        return
    print("Assignments:")
    for item in data["assignments"]:
        print(f"  - {item['package']} kind={item.get('assignment_kind')} until={item.get('allowed_until')} stop_before={item.get('stop_before')} next={item.get('next_action')}")
        print(f"    context: {', '.join(item.get('context_files', []))}")
        print(f"    prompt: {item.get('worker_prompt')}")