from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .package_state import create_package
from .schema import *
from .state import add_phase_history, ensure_execution
from .templates import map_template
from .validation import validate_package


def base_map_json(initiative: str, title: str, timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": MAP_SCHEMA_VERSION,
        "initiative": initiative,
        "title": title,
        "map_path": parent_map_ref(initiative),
        "status": "draft",
        "created_at": timestamp,
        "updated_at": timestamp,
        "packages": [],
        "orchestration": {
            "default_max_parallel": 3,
            "strategy": "lead-owned-rolling-worker-pool",
            "runtime": "claude-code-agent-team",
            "dependency_gate": "map-time parallel_policy decides whether dependency-incomplete packages may prepare; impl/review require satisfied gates",
            "execution_isolation": "each package worker runs as an Agent Team teammate with worktree isolation",
            "context_injection": "map.md + map.json + worker-dispatch.md + package task.json/prd/task/context + dependency summaries",
            "manual_review_mode": "use explicit brainstorm/task/impl/review skills instead of parallel",
        },
        "history": [
            {
                "at": timestamp,
                "actor": "arbor",
                "event": "map_created",
                "note": "initiative map workspace created",
            }
        ],
    }


def create_map(root: Path, initiative: str, title: str | None, timestamp: str, status: str | None = "draft") -> dict[str, Any]:
    validate_name(initiative)
    if status is not None and status not in {"draft", "active", "ready", "closed", "superseded"}:
        raise ArborError(f"Invalid map status '{status}'.")
    title = title or initiative
    directory = map_dir(root, initiative)
    context_dir = map_context_dir(root, initiative)
    context_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    md_path = map_path(root, initiative)
    legacy_path = legacy_map_path(root, initiative)
    if not md_path.exists():
        if legacy_path.exists():
            md_path.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            md_path.write_text(map_template(initiative, title, timestamp), encoding="utf-8")
        created.append("map.md")

    json_path = map_json_path(root, initiative)
    if json_path.exists():
        data = read_json(json_path)
        data.setdefault("schema_version", MAP_SCHEMA_VERSION)
        data.setdefault("initiative", initiative)
        data.setdefault("title", title)
        data.setdefault("map_path", parent_map_ref(initiative))
        data.setdefault("packages", [])
        orchestration = data.setdefault("orchestration", base_map_json(initiative, title, timestamp)["orchestration"])
        if isinstance(orchestration, dict):
            defaults = base_map_json(initiative, title, timestamp)["orchestration"]
            for key, value in defaults.items():
                orchestration.setdefault(key, value)
            if orchestration.get("strategy") in {"ready-packages-only", "autonomous-package-pipeline", "agent-team-worktree-pipeline"}:
                orchestration["strategy"] = "lead-owned-rolling-worker-pool"
            if orchestration.get("default_max_parallel") == 2:
                orchestration["default_max_parallel"] = 3
            orchestration.setdefault("runtime", "claude-code-agent-team")
            orchestration.setdefault("execution_isolation", "each package worker runs as an Agent Team teammate with worktree isolation")
        data.setdefault("history", [])
        if status is not None:
            data["status"] = status
        else:
            data.setdefault("status", "draft")
        data["updated_at"] = timestamp
    else:
        data = base_map_json(initiative, title, timestamp)
        data["status"] = status
        created.append("map.json")
    write_json(json_path, data)

    assignments_path = context_dir / "agent-assignments.jsonl"
    if write_if_missing(assignments_path, ""):
        created.append("context/agent-assignments.jsonl")

    return {"initiative": initiative, "map": parent_map_ref(initiative), "map_json": f".arbor/maps/{initiative}/map.json", "created": created}


def ensure_map_workspace(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    if map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    if legacy_map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    raise ArborError(f"Missing initiative map: {map_path(root, initiative)}")


def default_parallel_policy(depends_on: list[str], reason: str) -> dict[str, Any]:
    if depends_on:
        return {
            "independence": "contract_dependent",
            "can_prepare_without_dependencies": True,
            "can_implement_without_dependencies": False,
            "max_phase_before_dependencies": "task",
            "dependency_gate_phase": "impl",
            "reason": reason or "dependencies provide implementation contracts; package-local brainstorm/task can run before dependency completion",
        }
    return {
        "independence": "independent",
        "can_prepare_without_dependencies": True,
        "can_implement_without_dependencies": True,
        "max_phase_before_dependencies": "review",
        "dependency_gate_phase": "none",
        "reason": reason or "no package dependencies; can run independently through review",
    }


def normalize_parallel_policy(value: Any, depends_on: list[str], boundary_reason: str) -> dict[str, Any]:
    default = default_parallel_policy(depends_on, boundary_reason)
    if not isinstance(value, dict):
        return default
    policy = default.copy()
    independence = value.get("independence")
    if independence in PARALLEL_INDEPENDENCE:
        policy["independence"] = independence
    can_prepare = value.get("can_prepare_without_dependencies")
    if isinstance(can_prepare, bool):
        policy["can_prepare_without_dependencies"] = can_prepare
    can_implement = value.get("can_implement_without_dependencies")
    if isinstance(can_implement, bool):
        policy["can_implement_without_dependencies"] = can_implement
    max_phase = value.get("max_phase_before_dependencies")
    if max_phase in PARALLEL_MAX_PHASES:
        policy["max_phase_before_dependencies"] = max_phase
    gate_phase = value.get("dependency_gate_phase")
    if gate_phase in PARALLEL_GATE_PHASES:
        policy["dependency_gate_phase"] = gate_phase
    reason = value.get("reason")
    if isinstance(reason, str) and reason:
        policy["reason"] = reason
    if policy.get("independence") == "independent":
        policy["can_prepare_without_dependencies"] = True
        policy["can_implement_without_dependencies"] = True
        policy["max_phase_before_dependencies"] = "review"
        policy["dependency_gate_phase"] = "none"
    elif policy.get("independence") == "hard_dependent":
        policy["can_prepare_without_dependencies"] = False
        policy["can_implement_without_dependencies"] = False
    return policy


def parse_split_package_spec(raw: str) -> dict[str, Any]:
    parts = raw.split("::")
    if len(parts) not in {4, 8}:
        raise ArborError("Split package spec must use format name::title::dep1,dep2::boundary_reason or name::title::dep1,dep2::boundary_reason::independence::max_phase::gate_phase::parallel_reason.")
    name, title, deps_raw, boundary_reason = [part.strip() for part in parts[:4]]
    validate_name(name)
    if not title:
        raise ArborError(f"Split package '{name}' requires a title.")
    if not boundary_reason:
        raise ArborError(f"Split package '{name}' requires a boundary reason.")
    depends_on = [item.strip() for item in deps_raw.split(",") if item.strip()]
    for dep in depends_on:
        validate_name(dep)
        if dep == name:
            raise ArborError(f"Split package '{name}' cannot depend on itself.")
    policy = default_parallel_policy(depends_on, boundary_reason)
    if len(parts) == 8:
        independence, max_phase, gate_phase, parallel_reason = [part.strip() for part in parts[4:]]
        if independence:
            if independence not in PARALLEL_INDEPENDENCE:
                raise ArborError(f"Split package '{name}' has invalid independence: {independence}.")
            policy["independence"] = independence
        if max_phase:
            if max_phase not in PARALLEL_MAX_PHASES:
                raise ArborError(f"Split package '{name}' has invalid max phase: {max_phase}.")
            policy["max_phase_before_dependencies"] = max_phase
        if gate_phase:
            if gate_phase not in PARALLEL_GATE_PHASES:
                raise ArborError(f"Split package '{name}' has invalid dependency gate phase: {gate_phase}.")
            policy["dependency_gate_phase"] = gate_phase
        if parallel_reason:
            policy["reason"] = parallel_reason
        policy = normalize_parallel_policy(policy, depends_on, boundary_reason)
    return {"name": name, "title": title, "depends_on_packages": depends_on, "boundary_reason": boundary_reason, "parallel_policy": policy}


def ensure_same_or_empty(value: Any, expected: str, label: str, package_name: str) -> None:
    if value not in {None, expected}:
        raise ArborError(f"Package '{package_name}' already has {label}={value!r}; expected {expected!r}.")


def ensure_parent_map_same_or_legacy(value: Any, initiative: str, label: str, package_name: str) -> None:
    expected = parent_map_ref(initiative)
    legacy = legacy_parent_map_ref(initiative)
    if value not in {None, expected, legacy}:
        raise ArborError(f"Package '{package_name}' already has {label}={value!r}; expected {expected!r}.")


def package_map_entry(spec: dict[str, Any], timestamp: str) -> dict[str, Any]:
    name = spec["name"]
    return {
        "name": name,
        "title": spec["title"],
        "path": f".arbor/tasks/{name}",
        "materialized": True,
        "depends_on": spec["depends_on_packages"],
        "wave": spec.get("wave") or None,
        "boundary_reason": spec["boundary_reason"],
        "parallel_policy": normalize_parallel_policy(spec.get("parallel_policy"), spec["depends_on_packages"], spec["boundary_reason"]),
        "contract_inputs": [],
        "contract_outputs": [],
        "prd_status": "draft",
        "task_state": "planned",
        "execution_status": "unclaimed",
        "next_action": {"skill": "brainstorm", "task_id": None},
        "updated_at": timestamp,
    }


def upsert_map_packages(root: Path, initiative: str, specs: list[dict[str, Any]], actor: str, decision: str, timestamp: str) -> dict[str, Any]:
    workspace = create_map(root, initiative, initiative, timestamp, status="active")
    data = read_json(map_json_path(root, initiative))
    packages = data.get("packages")
    if not isinstance(packages, list):
        packages = []
    by_name: dict[str, dict[str, Any]] = {item.get("name"): item for item in packages if isinstance(item, dict) and isinstance(item.get("name"), str)}
    ordered_names = [item.get("name") for item in packages if isinstance(item, dict) and isinstance(item.get("name"), str)]
    for spec in specs:
        name = spec["name"]
        entry = by_name.get(name, {})
        entry.update(package_map_entry(spec, timestamp))
        by_name[name] = entry
        if name not in ordered_names:
            ordered_names.append(name)
    data["packages"] = [by_name[name] for name in ordered_names]
    data["updated_at"] = timestamp
    data.setdefault("history", []).append({"at": timestamp, "actor": actor, "event": "packages_materialized", "note": decision, "packages": [spec["name"] for spec in specs]})
    write_json(map_json_path(root, initiative), data)
    return workspace


def create_split_packages(root: Path, initiative: str, package_specs: list[str], actor: str, mode: str, decision: str, timestamp: str) -> dict[str, Any]:
    validate_name(initiative)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'.")
    if not decision:
        raise ArborError("create-split-packages requires a non-empty decision.")
    ensure_map_workspace(root, initiative, timestamp)

    specs = [parse_split_package_spec(raw) for raw in package_specs]
    seen: set[str] = set()
    spec_names = {spec["name"] for spec in specs}
    for spec in specs:
        name = spec["name"]
        if name == initiative:
            raise ArborError("Split package name must not equal the parent initiative name.")
        if name in seen:
            raise ArborError(f"Duplicate split package: {name}")
        seen.add(name)
        for dep in spec["depends_on_packages"]:
            if dep not in spec_names and not package_dir(root, dep).exists():
                raise ArborError(f"Split package '{name}' depends on unknown package '{dep}'.")

    parent_map = parent_map_ref(initiative)
    for spec in specs:
        name = spec["name"]
        pkg_path = package_dir(root, name)
        if (pkg_path / "task.json").exists():
            existing = read_json(pkg_path / "task.json")
            existing_prd = existing.get("prd") if isinstance(existing.get("prd"), dict) else {}
            existing_sizing = existing.get("package_sizing") if isinstance(existing.get("package_sizing"), dict) else {}
            ensure_same_or_empty(existing_prd.get("parent_initiative"), initiative, "prd.parent_initiative", name)
            ensure_parent_map_same_or_legacy(existing_prd.get("parent_map"), initiative, "prd.parent_map", name)
            ensure_same_or_empty(existing_sizing.get("parent_initiative"), initiative, "package_sizing.parent_initiative", name)
            ensure_parent_map_same_or_legacy(existing_sizing.get("parent_map"), initiative, "package_sizing.parent_map", name)
            existing_status = existing_sizing.get("status")
            if existing_status not in {None, "unchecked", "split_applied"}:
                raise ArborError(f"Package '{name}' already has incompatible package_sizing.status={existing_status!r}.")

    upsert_map_packages(root, initiative, specs, actor, decision, timestamp)
    materialized: list[dict[str, Any]] = []
    for spec in specs:
        name = spec["name"]
        result = create_package(root, name, mode, spec["title"], "map-split", timestamp)
        pkg, data = load_package(root, name)
        prd = data.setdefault("prd", {})
        prd["source_type"] = "map-split"
        prd["parent_map"] = parent_map
        prd["parent_initiative"] = initiative
        prd.setdefault("status", "draft")
        prd.setdefault("ready_for_task_at", None)
        old = data.get("package_sizing", {}).get("status") if isinstance(data.get("package_sizing"), dict) else None
        data["package_sizing"] = {
            "status": "split_applied",
            "decision": decision,
            "signals": ["materialized_from_map"],
            "recommended_packages": [],
            "parent_map": parent_map,
            "parent_initiative": initiative,
            "depends_on_packages": spec["depends_on_packages"],
            "boundary_reason": spec["boundary_reason"],
            "parallel_policy": normalize_parallel_policy(spec.get("parallel_policy"), spec["depends_on_packages"], spec["boundary_reason"]),
            "decided_at": timestamp,
            "decided_by": actor,
            "note": f"materialized from {parent_map}",
        }
        data["state"] = "planned"
        data["current_phase"] = "brainstorm"
        data["active_task"] = None
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "map-split child package PRD draft"}
        data["updated_at"] = timestamp
        add_phase_history(data, timestamp, "map", None, old, "package_sizing:split_applied", actor, f"materialized from {parent_map}")
        save_package(pkg, data)
        materialized.append({"name": name, "path": f".arbor/tasks/{name}", "created": result["created"], "depends_on_packages": spec["depends_on_packages"]})

    sync_map_from_packages(root, initiative, timestamp)
    return {"initiative": initiative, "map": parent_map, "map_json": f".arbor/maps/{initiative}/map.json", "packages": materialized}


def read_package_summary(root: Path, name: str) -> dict[str, Any]:
    pkg = package_dir(root, name)
    if not (pkg / "task.json").exists():
        return {
            "name": name,
            "path": f".arbor/tasks/{name}",
            "exists": False,
            "validation": {"ok": False, "errors": ["package task.json missing"]},
        }
    data = read_json(pkg / "task.json")
    errors = validate_package(root, name)
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    execution = ensure_execution(data)
    checkpoints = execution.get("checkpoints") if isinstance(execution.get("checkpoints"), list) else []
    latest_checkpoint = checkpoints[-1] if checkpoints and isinstance(checkpoints[-1], dict) else None
    prd = data.get("prd") if isinstance(data.get("prd"), dict) else {}
    sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
    next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else {}
    return {
        "name": name,
        "title": data.get("title") or name,
        "path": f".arbor/tasks/{name}",
        "exists": True,
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "prd_status": prd.get("status"),
        "package_sizing": sizing.get("status"),
        "depends_on": sizing.get("depends_on_packages", []) if isinstance(sizing.get("depends_on_packages", []), list) else [],
        "parallel_policy": normalize_parallel_policy(sizing.get("parallel_policy"), sizing.get("depends_on_packages", []) if isinstance(sizing.get("depends_on_packages", []), list) else [], sizing.get("boundary_reason") if isinstance(sizing.get("boundary_reason"), str) else ""),
        "parent_initiative": prd.get("parent_initiative") or sizing.get("parent_initiative"),
        "next_action": {"skill": next_action.get("skill"), "task_id": next_action.get("task_id"), "reason": next_action.get("reason")},
        "execution_status": execution.get("status"),
        "execution_owner": execution.get("owner"),
        "latest_checkpoint": latest_checkpoint,
        "pr_state": execution.get("pr", {}).get("state") if isinstance(execution.get("pr"), dict) else None,
        "task_count": len(tasks),
        "ready_count": sum(1 for task in tasks if task.get("state") == "ready"),
        "blocked_count": sum(1 for task in tasks if task.get("state") in {"blocked", "needs_context"}),
        "validation": {"ok": not errors, "errors": errors},
    }


def map_package_names(root: Path, initiative: str, data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for entry in data.get("packages", []) if isinstance(data.get("packages"), list) else []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"] not in names:
            names.append(entry["name"])
    root_dir = tasks_root(root)
    if root_dir.exists():
        for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
            task_path = pkg / "task.json"
            if not task_path.exists():
                continue
            try:
                task_data = read_json(task_path)
            except ArborError:
                continue
            prd = task_data.get("prd") if isinstance(task_data.get("prd"), dict) else {}
            sizing = task_data.get("package_sizing") if isinstance(task_data.get("package_sizing"), dict) else {}
            if initiative in {prd.get("parent_initiative"), sizing.get("parent_initiative")} and pkg.name not in names:
                names.append(pkg.name)
    return names


def sync_map_from_packages(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    ensure_map_workspace(root, initiative, timestamp)
    json_path = map_json_path(root, initiative)
    data = read_json(json_path)
    existing_entries = data.get("packages", []) if isinstance(data.get("packages"), list) else []
    by_name: dict[str, dict[str, Any]] = {entry.get("name"): entry for entry in existing_entries if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    names = map_package_names(root, initiative, data)
    synced: list[dict[str, Any]] = []
    for name in names:
        entry = by_name.get(name, {"name": name, "path": f".arbor/tasks/{name}"})
        summary = read_package_summary(root, name)
        if summary.get("exists"):
            entry["title"] = summary.get("title") or entry.get("title") or name
            entry["path"] = summary.get("path")
            entry["materialized"] = True
            entry["depends_on"] = summary.get("depends_on", entry.get("depends_on", []))
            entry["parallel_policy"] = normalize_parallel_policy(entry.get("parallel_policy") or summary.get("parallel_policy"), entry.get("depends_on", []), entry.get("boundary_reason") or "")
            entry["prd_status"] = summary.get("prd_status")
            entry["task_state"] = summary.get("state")
            entry["current_phase"] = summary.get("current_phase")
            entry["execution_status"] = summary.get("execution_status")
            entry["execution_owner"] = summary.get("execution_owner")
            entry["latest_checkpoint"] = summary.get("latest_checkpoint")
            entry["next_action"] = summary.get("next_action")
            entry["task_count"] = summary.get("task_count")
            entry["ready_count"] = summary.get("ready_count")
            entry["blocked_count"] = summary.get("blocked_count")
            entry["validation"] = summary.get("validation")
        else:
            entry.setdefault("path", f".arbor/tasks/{name}")
            entry["materialized"] = False
            entry["validation"] = summary.get("validation")
        entry.setdefault("wave", None)
        entry.setdefault("boundary_reason", None)
        entry["parallel_policy"] = normalize_parallel_policy(entry.get("parallel_policy"), entry.get("depends_on", []) if isinstance(entry.get("depends_on"), list) else [], entry.get("boundary_reason") or "")
        entry.setdefault("contract_inputs", [])
        entry.setdefault("contract_outputs", [])
        entry["updated_at"] = timestamp
        synced.append(entry)
    data["packages"] = synced
    data["updated_at"] = timestamp
    write_json(json_path, data)
    return data


def package_dependency_complete(summary: dict[str, Any]) -> bool:
    return summary.get("state") in {"reviewed", "completed"} or summary.get("execution_status") in {"reviewed", "merged"} or summary.get("pr_state") == "merged"


def package_active(summary: dict[str, Any]) -> bool:
    return summary.get("state") == "in_progress" or summary.get("execution_status") in {"claimed", "worktree_ready", "in_progress", "pr_open"}


def package_assignable(summary: dict[str, Any]) -> bool:
    if not summary.get("exists"):
        return False
    if not summary.get("validation", {}).get("ok"):
        return False
    if package_dependency_complete(summary) or package_active(summary):
        return False
    if summary.get("state") in {"blocked", "needs_context", "superseded"}:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    return next_action.get("skill") in {"brainstorm", "task", "impl", "review"}


def dependency_gate_satisfied(dependency_blockers: list[dict[str, Any]]) -> bool:
    return not dependency_blockers


def phase_before_dependency_allowed(skill: Any, max_phase: Any) -> bool:
    order = {"brainstorm": 1, "task": 2, "impl": 3, "review": 4}
    return isinstance(skill, str) and isinstance(max_phase, str) and order.get(skill, 999) <= order.get(max_phase, 0)


def package_prep_assignable(summary: dict[str, Any], policy: dict[str, Any], dependency_blockers: list[dict[str, Any]]) -> bool:
    if not package_assignable(summary) or not dependency_blockers:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    skill = next_action.get("skill")
    return bool(policy.get("can_prepare_without_dependencies")) and skill in {"brainstorm", "task"} and phase_before_dependency_allowed(skill, policy.get("max_phase_before_dependencies"))


def package_execution_assignable(summary: dict[str, Any], policy: dict[str, Any], dependency_blockers: list[dict[str, Any]]) -> bool:
    if not package_assignable(summary):
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    skill = next_action.get("skill")
    if dependency_gate_satisfied(dependency_blockers):
        return skill in {"brainstorm", "task", "impl", "review"}
    return bool(policy.get("can_implement_without_dependencies")) and skill in {"impl", "review"} and phase_before_dependency_allowed(skill, policy.get("max_phase_before_dependencies"))


def wave_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    wave = entry.get("wave")
    if isinstance(wave, str):
        match = re.search(r"\d+", wave)
        if match:
            return (int(match.group()), wave, entry.get("name", ""))
    return (999, str(wave or ""), entry.get("name", ""))


def map_check(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    data = sync_map_from_packages(root, initiative, timestamp)
    summaries = {entry["name"]: read_package_summary(root, entry["name"]) for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    package_entries = {entry["name"]: entry for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    execution_ready: list[dict[str, Any]] = []
    prep_ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for name in sorted(summaries, key=lambda item: wave_sort_key(package_entries.get(item, {"name": item}))):
        summary = summaries[name]
        entry = package_entries.get(name, {"name": name})
        deps = entry.get("depends_on", summary.get("depends_on", []))
        policy = normalize_parallel_policy(entry.get("parallel_policy") or summary.get("parallel_policy"), deps if isinstance(deps, list) else [], entry.get("boundary_reason") or "")
        dependency_blockers: list[dict[str, Any]] = []
        for dep in deps if isinstance(deps, list) else []:
            dep_summary = summaries.get(dep) if dep in summaries else read_package_summary(root, dep)
            if not package_dependency_complete(dep_summary):
                dependency_blockers.append({"name": dep, "state": dep_summary.get("state"), "exists": dep_summary.get("exists"), "execution_status": dep_summary.get("execution_status"), "latest_checkpoint": dep_summary.get("latest_checkpoint")})

        item = {
            "name": name,
            "path": summary.get("path"),
            "wave": entry.get("wave"),
            "state": summary.get("state"),
            "prd_status": summary.get("prd_status"),
            "execution_status": summary.get("execution_status"),
            "latest_checkpoint": summary.get("latest_checkpoint"),
            "next_action": summary.get("next_action"),
            "depends_on": deps if isinstance(deps, list) else [],
            "parallel_policy": policy,
            "validation": summary.get("validation"),
        }
        if not summary.get("exists"):
            item["reason"] = "package stub missing"
            missing.append(item)
        elif package_dependency_complete(summary):
            complete.append(item)
        elif package_active(summary):
            item["reason"] = "package already claimed or in progress"
            active.append(item)
        elif not summary.get("validation", {}).get("ok"):
            item["reason"] = "package validation failed"
            blocked.append(item)
        elif summary.get("state") in {"blocked", "needs_context", "superseded"}:
            item["reason"] = f"package state is {summary.get('state')}"
            blocked.append(item)
        elif package_execution_assignable(summary, policy, dependency_blockers):
            item["assignment_kind"] = "execution_ready"
            item["allowed_until"] = "review"
            item["stop_before"] = None
            item["dependency_gate"] = "satisfied" if dependency_gate_satisfied(dependency_blockers) else "implementation_allowed_by_policy"
            if dependency_blockers:
                item["blocked_by"] = dependency_blockers
            execution_ready.append(item)
        elif package_prep_assignable(summary, policy, dependency_blockers):
            item["assignment_kind"] = "prep_ready"
            item["allowed_until"] = policy.get("max_phase_before_dependencies") or "task"
            item["stop_before"] = policy.get("dependency_gate_phase") or "impl"
            item["dependency_gate"] = "planning-only"
            item["blocked_by"] = dependency_blockers
            prep_ready.append(item)
        elif dependency_blockers:
            item["reason"] = "dependency gate not satisfied"
            item["blocked_by"] = dependency_blockers
            blocked.append(item)
        elif package_assignable(summary):
            item["reason"] = "parallel policy does not allow current next action"
            blocked.append(item)
        else:
            item["reason"] = "no assignable next action"
            blocked.append(item)

    return {
        "initiative": initiative,
        "map": parent_map_ref(initiative),
        "map_json": f".arbor/maps/{initiative}/map.json",
        "execution_ready": execution_ready,
        "prep_ready": prep_ready,
        "ready": execution_ready + prep_ready,
        "blocked": blocked,
        "active": active,
        "complete": complete,
        "missing": missing,
    }


def team_name_for_initiative(initiative: str) -> str:
    validate_name(initiative)
    return f"arbor-{initiative}"


def worker_name_for_package(name: str) -> str:
    validate_name(name)
    return f"pipeline-{name}"


def package_branch_name(initiative: str, name: str) -> str:
    validate_name(initiative)
    validate_name(name)
    return f"arbor/{initiative}/{name}"


def package_worktree_hint(initiative: str, name: str) -> str:
    validate_name(initiative)
    validate_name(name)
    return f".claude/worktrees/arbor-{initiative}/{name}"


def worker_dispatch_path(name: str) -> str:
    validate_name(name)
    return f".arbor/tasks/{name}/context/worker-dispatch.md"


def build_worker_dispatch_markdown(initiative: str, name: str, summary: dict[str, Any], deps: list[dict[str, Any]], assignment: dict[str, Any]) -> str:
    dependency_lines = "\n".join(
        f"- {dep.get('name')}: state={dep.get('state')} prd={dep.get('prd_status')} execution={dep.get('execution_status')} checkpoint={dep.get('latest_checkpoint')} path={dep.get('path')}"
        for dep in deps
    ) or "- none"
    context_lines = "\n".join(f"- `{path}`" for path in assignment["context_files"])
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    stop_line = f"- Stop before: `{assignment['stop_before']}`" if assignment.get("stop_before") else "- Stop before: none"
    return f"""# Worker dispatch: {name}

使用语言：中文。

- Initiative: `{initiative}`
- Team runtime: `{assignment['team_name']}`
- Worker: `{assignment['worker_name']}`
- Package: `{name}`
- Workflow package path: `.arbor/tasks/{name}/`
- Assignment kind: `{assignment['assignment_kind']}`
- Allowed until: `{assignment['allowed_until']}`
{stop_line}
- Dependency gate: `{assignment['dependency_gate']}`
- Branch: `{assignment['branch']}`
- Worktree hint: `{assignment['worktree_hint']}`
- Current phase: `{summary.get('current_phase')}`
- Next action: `{next_action.get('skill')}` task `{next_action.get('task_id')}` — {next_action.get('reason')}

## Required context

{context_lines}

## Dependency summaries

{dependency_lines}

## Team coordination

- Use `TaskUpdate` for shared Team task runtime status.
- Use `SendMessage` to report start, completion, blockers, and contract questions to the lead.
- You may message producer/consumer package workers for contract questions.
- Team messages coordinate work; durable decisions belong in `.arbor` package state or amendments.

If this package needs a producer package change:
1. Message the producer worker and the lead.
2. Pause this package before implementing against missing behavior.
3. Producer owns its amendment/patch and checkpoint.
4. Resume only after the lead reports an updated checkpoint/base.

## Worker contract

1. The main Claude session is the lead/orchestrator; this Team is only the runtime worker pool and shared task list.
2. Run as worker teammate in the package worktree, not in the lead/orchestrator worktree.
3. Own only this package boundary and its code changes; do not mutate sibling package state.
4. Advance `task.json.next_action` only up to the assignment limit. If `stop_before` is set, stop and report before entering that phase.
5. For clear package-local drift, use forward-only amendment: append AMD-xxx, append linked T-xxx, then continue within the assignment limit.
6. Do not create PRs, push, deploy, delete data, or perform destructive actions unless the user explicitly authorizes that action.
7. Stop and report to the lead on ambiguity, package boundary drift, missing dependency contract, failing/unavailable acceptance, or unsafe external side effects.
"""


def write_worker_dispatch_packet(root: Path, initiative: str, name: str, summary: dict[str, Any], deps: list[dict[str, Any]], assignment: dict[str, Any]) -> str:
    path = root / worker_dispatch_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_worker_dispatch_markdown(initiative, name, summary, deps, assignment), encoding="utf-8")
    return worker_dispatch_path(name)


def assignment_context(root: Path, initiative: str, item: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    name = item["name"]
    summary = read_package_summary(root, name)
    deps = item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []
    dependency_summaries = [read_package_summary(root, dep) for dep in deps]
    team_name = team_name_for_initiative(initiative)
    worker_name = worker_name_for_package(name)
    assignment = {
        "initiative": initiative,
        "package": name,
        "package_path": f".arbor/tasks/{name}",
        "team_name": team_name,
        "worker_name": worker_name,
        "runtime": "claude-code-agent-team",
        "isolation": "worktree",
        "assignment_kind": item.get("assignment_kind", "execution_ready"),
        "allowed_until": item.get("allowed_until", "review"),
        "stop_before": item.get("stop_before"),
        "dependency_gate": item.get("dependency_gate", "satisfied"),
        "parallel_policy": item.get("parallel_policy"),
        "branch": package_branch_name(initiative, name),
        "base_branch": None,
        "worktree_hint": package_worktree_hint(initiative, name),
        "next_action": item.get("next_action"),
        "context_files": [
            parent_map_ref(initiative),
            f".arbor/maps/{initiative}/map.json",
            worker_dispatch_path(name),
            f".arbor/tasks/{name}/prd.md",
            f".arbor/tasks/{name}/task.md",
            f".arbor/tasks/{name}/task.json",
            f".arbor/tasks/{name}/context/impl.jsonl",
            f".arbor/tasks/{name}/context/review.jsonl",
            f".arbor/tasks/{name}/context/sources.jsonl",
        ],
        "dependency_summaries": [
            {
                "name": dep.get("name"),
                "state": dep.get("state"),
                "prd_status": dep.get("prd_status"),
                "execution_status": dep.get("execution_status"),
                "latest_checkpoint": dep.get("latest_checkpoint"),
                "path": dep.get("path"),
            }
            for dep in dependency_summaries
        ],
    }
    write_worker_dispatch_packet(root, initiative, name, summary, dependency_summaries, assignment)
    stop_clause = f" Stop before entering {assignment['stop_before']}." if assignment.get("stop_before") else ""
    assignment["worker_prompt"] = (
        "使用语言：中文。 "
        f"Act as Agent Team worker teammate '{worker_name}' for sdd-kit package '{name}' in team runtime '{team_name}'. "
        "The main Claude session is the lead/orchestrator; do not create a nested orchestrator agent. "
        f"Use worktree isolation for branch '{assignment['branch']}' (worktree hint: {assignment['worktree_hint']}). "
        f"First read {worker_dispatch_path(name)}, then the map and package-local PRD/task/task.json/context files listed there. "
        f"This assignment is {assignment['assignment_kind']}: advance from task.json next_action={summary.get('next_action', {}).get('skill')} up to {assignment['allowed_until']}.{stop_clause} "
        "Use TaskUpdate for the shared Team task and SendMessage for start/completion/blockers. "
        "Message teammate workers for producer/consumer contract questions, but never mutate sibling package state or patch producer packages directly. "
        "If reviewed package work is ready, ask the lead to integrate and record a checkpoint. "
        "Do not start downstream packages, write product code under .arbor/tasks, create PRs, push, deploy, or take destructive actions."
    )
    return assignment


def map_plan_agents(root: Path, initiative: str, max_parallel: int, actor: str, timestamp: str) -> dict[str, Any]:
    if max_parallel < 1:
        raise ArborError("--max-parallel must be at least 1.")
    if max_parallel > 3:
        raise ArborError("--max-parallel must be 3 or less; keep the lead-owned worker pool bounded.")
    check = map_check(root, initiative, timestamp)
    assignments = []
    candidates = check["execution_ready"] + check["prep_ready"]
    for item in candidates[:max_parallel]:
        assignments.append(assignment_context(root, initiative, item, check))
    plan = {
        "at": timestamp,
        "actor": actor,
        "initiative": initiative,
        "team_name": team_name_for_initiative(initiative),
        "runtime": "claude-code-agent-team",
        "lead": "main-session",
        "max_parallel": max_parallel,
        "strategy": "lead-owned-rolling-worker-pool",
        "assignments": assignments,
        "execution_ready_count": len(check["execution_ready"]),
        "prep_ready_count": len(check["prep_ready"]),
        "blocked_count": len(check["blocked"]),
        "active_count": len(check["active"]),
        "complete_count": len(check["complete"]),
    }
    append_jsonl(map_context_dir(root, initiative) / "agent-assignments.jsonl", plan)
    return plan