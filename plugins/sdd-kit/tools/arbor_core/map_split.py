from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import add_phase_history, ensure_execution
from .package_model import create_package
from .map_model import create_map, ensure_map_workspace
from .map_policy import default_parallel_policy, normalize_modification_scope, normalize_parallel_policy, normalize_string_list
from .map_sync import sync_map_from_packages


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
        "modification_scope": normalize_modification_scope(spec.get("modification_scope"), name, spec["boundary_reason"]),
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
        preserved_scope = entry.get("modification_scope")
        preserved_inputs = entry.get("contract_inputs")
        preserved_outputs = entry.get("contract_outputs")
        new_entry = package_map_entry(spec, timestamp)
        if preserved_scope is not None:
            new_entry["modification_scope"] = normalize_modification_scope(preserved_scope, name, spec["boundary_reason"])
        if preserved_inputs is not None:
            new_entry["contract_inputs"] = normalize_string_list(preserved_inputs)
        if preserved_outputs is not None:
            new_entry["contract_outputs"] = normalize_string_list(preserved_outputs)
        entry.update(new_entry)
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
            "note": f"由 {parent_map} 拆包 materialize",
        }
        data["state"] = "planned"
        data["current_phase"] = "brainstorm"
        data["active_task"] = None
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "map 已拆出 child package，下一步由 brainstorm 补齐 package-local PRD"}
        execution = ensure_execution(data)
        execution["modification_scope"] = normalize_modification_scope(execution.get("modification_scope") or spec.get("modification_scope"), name, spec["boundary_reason"])
        execution["contract_inputs"] = normalize_string_list(execution.get("contract_inputs"))
        execution["contract_outputs"] = normalize_string_list(execution.get("contract_outputs"))
        data["updated_at"] = timestamp
        add_phase_history(data, timestamp, "map", None, old, "package_sizing:split_applied", actor, f"由 {parent_map} 拆包 materialize")
        save_package(pkg, data)
        materialized.append({"name": name, "path": f".arbor/tasks/{name}", "created": result["created"], "depends_on_packages": spec["depends_on_packages"]})

    sync_map_from_packages(root, initiative, timestamp)
    return {"initiative": initiative, "map": parent_map, "map_json": f".arbor/maps/{initiative}/map.json", "packages": materialized}
