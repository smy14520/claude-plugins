from __future__ import annotations

def print_human_list(items: list[dict[str, Any]]) -> None:
    if not items:
        print("未找到 task package。")
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
        "execution_ready": "可执行",
        "prep_ready": "可准备",
        "integration_ready": "可串行集成",
        "active": "执行中",
        "blocked": "阻塞",
        "missing": "缺失",
        "complete": "完成",
    }
    for label in ["execution_ready", "prep_ready", "integration_ready", "active", "blocked", "missing", "complete"]:
        print(f"{labels[label]}:")
        items = data.get(label, [])
        if not items:
            print("  - 无")
            continue
        for item in items:
            detail = item.get("reason") or item.get("assignment_kind") or item.get("next_action", {}).get("skill") or item.get("state")
            limit = f" allowed_until={item.get('allowed_until')} stop_before={item.get('stop_before')}" if item.get("assignment_kind") else ""
            role = (item.get("modification_scope") or {}).get("integration_role") if isinstance(item.get("modification_scope"), dict) else None
            role_detail = f" role={role}" if role else ""
            print(f"  - {item.get('name')} wave={item.get('wave')} state={item.get('state')} exec={item.get('execution_status')}{role_detail} detail={detail}{limit}")
            for blocker in item.get("blocked_by", []) if isinstance(item.get("blocked_by"), list) else []:
                print(f"      blocked_by {blocker.get('name')} state={blocker.get('state')} exec={blocker.get('execution_status')} lead_checkpoint={blocker.get('latest_lead_checkpoint')}")


def print_human_agent_plan(data: dict[str, Any]) -> None:
    print(f"Initiative: {data['initiative']}")
    print(f"Round: {data.get('round_id')}")
    print(f"Strategy: {data['strategy']} max_parallel={data['max_parallel']} lead={data.get('lead')}")
    print(f"Team runtime: {data.get('team_name')} runtime={data.get('runtime')} isolation={data.get('isolation', 'enter-worktree-gate')}")
    if data.get("worktree_root_ref"):
        print(f"Worktree root: ref={data.get('worktree_root_ref')} path={data.get('worktree_root_path')}")
    print("模式: main-session lead + bounded rolling Agent Team worker pool；需要人工 gate 时使用显式阶段 skill")
    reconciliation = data.get("runtime_reconciliation") if isinstance(data.get("runtime_reconciliation"), dict) else {}
    if reconciliation:
        print("Runtime reconciliation:")
        for key, value in reconciliation.items():
            print(f"  - {key}: {value}")
    integration_ready = data.get("integration_ready", []) if isinstance(data.get("integration_ready"), list) else []
    if integration_ready:
        print("可串行集成（serial integration worker lane；lead 只审查/checkpoint）:")
        for item in integration_ready:
            print(f"  - {item.get('name')} detail={item.get('reason')}")
    integration_assignments = data.get("integration_assignments", []) if isinstance(data.get("integration_assignments"), list) else []
    if integration_assignments:
        print("串行集成派发（lead 一次只派一个 serial integration worker）:")
        for item in integration_assignments:
            print(f"  - {item.get('package')} id={item.get('assignment_id')} worker={item.get('worker_name')} next={item.get('next_action')}")
    if not data.get("assignments"):
        print("Assignments: 无")
        return
    print("Assignments:")
    for item in data["assignments"]:
        print(f"  - {item['package']} id={item.get('assignment_id')} kind={item.get('assignment_kind')} until={item.get('allowed_until')} stop_before={item.get('stop_before')} next={item.get('next_action')}")
        print(f"    worktree: ref={item.get('worktree_ref')} path={item.get('resolved_worktree_path')}")
        print(f"    context: {', '.join(item.get('context_files', []))}")
        print(f"    prompt: {item.get('worker_prompt')}")