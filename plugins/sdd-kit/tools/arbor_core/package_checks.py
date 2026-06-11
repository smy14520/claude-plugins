from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .prd_slices import VERIFICATION_KINDS, parse_verification_items
from .schema import SLICE_ID_RE

CHECK_STATUSES = {"passed", "failed", "blocked", "not_run"}
AUTOMATED_CHECK_KINDS = {"build", "test", "typecheck", "lint", "docker", "api"}
FUNCTIONAL_CHECK_KIND = "functional"

_BACKTICK_RE = re.compile(r"`([^`]+)`")
_CHECK_ID_RE = re.compile(r"^chk_(\d{3})$")
_REQUIRED_CHECK_FIELDS = ("id", "slice", "kind", "description", "required", "source", "command_hint", "fingerprint")


def _slice_files(pkg: Path) -> list[Path]:
    slices_dir = pkg / "slices"
    if not slices_dir.exists():
        return []
    return sorted(path for path in slices_dir.glob("S-*.md") if SLICE_ID_RE.match(path.stem))


def _command_hint(description: str) -> str | None:
    match = _BACKTICK_RE.search(description)
    if not match:
        return None
    return match.group(1).strip() or None


def _required_check_id(slice_id: str, index: int) -> str:
    return f"req_{slice_id.replace('-', '')}_{index:03d}"


def _required_fingerprint(check: dict[str, Any]) -> str:
    payload = {
        "slice": check.get("slice"),
        "kind": check.get("kind"),
        "description": check.get("description"),
        "source": check.get("source"),
        "command_hint": check.get("command_hint"),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _required_signature(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{field: item.get(field) for field in _REQUIRED_CHECK_FIELDS if field in item} for item in checks]


def _derive_required_checks_from_pkg(pkg: Path) -> list[dict[str, Any]]:
    """Derive required checks from slice task `## Verification` sections.

    Kind is read from the explicit `[kind]` tag declared by brainstorm; the
    CLI never infers it — kind decides gate strictness (automated kinds demand
    run-check evidence), which is policy, not parsing.
    """
    required: list[dict[str, Any]] = []
    untagged: list[str] = []
    for slice_file in _slice_files(pkg):
        slice_id = slice_file.stem
        text = slice_file.read_text(encoding="utf-8")
        for index, (kind, item) in enumerate(parse_verification_items(text), start=1):
            if kind is None:
                untagged.append(f"slices/{slice_file.name}: \"{item}\"")
                continue
            command_hint = _command_hint(item)
            check: dict[str, Any] = {
                "id": _required_check_id(slice_id, index),
                "slice": slice_id,
                "kind": kind,
                "description": item,
                "required": True,
                "source": f"slices/{slice_file.name}#Verification",
            }
            if command_hint:
                check["command_hint"] = command_hint
            check["fingerprint"] = _required_fingerprint(check)
            required.append(check)
    if untagged:
        kinds = "/".join(sorted(VERIFICATION_KINDS))
        raise ArborError(
            "Verification 项缺少显式 [kind] 标签: " + "; ".join(untagged)
            + f"。在 slice task 文件中写成 `- [test] ...` 形式，合法 kind: {kinds}。"
        )
    if not required:
        raise ArborError("No required checks found. Add ## Verification bullets to slice task files before recording DONE.")
    return required


def ensure_required_checks(pkg: Path, data: dict[str, Any], timestamp: str) -> list[dict[str, Any]]:
    required = _derive_required_checks_from_pkg(pkg)
    existing = data.get("required_checks")
    if isinstance(existing, list) and _required_signature([item for item in existing if isinstance(item, dict)]) == _required_signature(required):
        return existing
    data["required_checks"] = required
    data["updated_at"] = timestamp
    return required


def derive_required_checks(root: Path, name: str, actor: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    data["required_checks"] = _derive_required_checks_from_pkg(pkg)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "required_checks": data["required_checks"]}


def _next_check_id(data: dict[str, Any]) -> str:
    max_id = 0
    for item in data.get("checks", []):
        if not isinstance(item, dict):
            continue
        match = _CHECK_ID_RE.match(str(item.get("id", "")))
        if match:
            max_id = max(max_id, int(match.group(1)))
    return f"chk_{max_id + 1:03d}"


def _required_by_id(required_checks: list[dict[str, Any]], check_id: str) -> dict[str, Any]:
    for item in required_checks:
        if item.get("id") == check_id:
            return item
    raise ArborError(f"Unknown required check id '{check_id}'. Run derive-required-checks to inspect expected ids.")


def _validate_recorded_check(status: str, evidence: list[str], reason: str, command: str | None, exit_code: int | None) -> None:
    if status not in CHECK_STATUSES:
        raise ArborError(f"Invalid check status '{status}'. Use: {', '.join(sorted(CHECK_STATUSES))}.")
    if status in {"blocked", "not_run"}:
        if not reason.strip():
            raise ArborError(f"Check status '{status}' requires --reason.")
        if not evidence and not command:
            raise ArborError(f"Check status '{status}' requires --evidence or --command showing why it could not run.")
    if status == "passed" and not evidence and not command:
        raise ArborError("Recorded passed checks require --evidence or --command.")
    if status == "passed" and exit_code not in (None, 0):
        raise ArborError("Passed checks cannot have non-zero --exit-code.")
    if status == "failed" and exit_code == 0:
        raise ArborError("Failed checks cannot have --exit-code 0.")


def record_check(
    root: Path,
    name: str,
    required_check: str | None,
    kind: str | None,
    slice_id: str | None,
    status: str,
    summary: str,
    evidence: list[str],
    reason: str,
    command: str | None,
    exit_code: int | None,
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    _validate_recorded_check(status, [item for item in evidence if item], reason, command, exit_code)
    pkg, data = load_package(root, name)
    required_checks = ensure_required_checks(pkg, data, timestamp)
    req: dict[str, Any] | None = None
    if required_check:
        req = _required_by_id(required_checks, required_check)
        kind = kind or str(req.get("kind", "manual"))
        slice_id = slice_id or str(req.get("slice", ""))
        summary = summary or str(req.get("description", ""))
    if not kind:
        raise ArborError("record-check requires --kind when --required-check is omitted.")
    if slice_id and not SLICE_ID_RE.match(slice_id):
        raise ArborError(f"Invalid slice id '{slice_id}'. Use S-001 format.")
    checks = data.setdefault("checks", [])
    if not isinstance(checks, list):
        raise ArborError("task.json checks must be a list.")
    entry: dict[str, Any] = {
        "id": _next_check_id(data),
        "source": "record-check",
        "status": status,
        "kind": kind,
        "summary": summary.strip(),
        "evidence": [item for item in evidence if item],
        "at": timestamp,
        "actor": actor,
    }
    if req is not None:
        entry["required_check"] = required_check
        entry["required_check_fingerprint"] = req.get("fingerprint")
    if slice_id:
        entry["slice"] = slice_id
    if reason.strip():
        entry["reason"] = reason.strip()
    if command:
        entry["command"] = command
    if exit_code is not None:
        entry["exit_code"] = exit_code
    checks.append(entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "check": entry}


def _normalize_command_args(command_args: list[str]) -> list[str]:
    if command_args and command_args[0] == "--":
        command_args = command_args[1:]
    if not command_args:
        raise ArborError("run-check requires a command after --.")
    return command_args


def _write_check_output(pkg: Path, check_id: str, stdout: str, stderr: str) -> tuple[str, str]:
    checks_dir = pkg / "checks"
    checks_dir.mkdir(exist_ok=True)
    stdout_path = checks_dir / f"{check_id}.stdout"
    stderr_path = checks_dir / f"{check_id}.stderr"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return (str(stdout_path.relative_to(pkg)), str(stderr_path.relative_to(pkg)))


def run_check(
    root: Path,
    name: str,
    required_check: str | None,
    kind: str | None,
    slice_id: str | None,
    cwd: str | None,
    timeout: int,
    command_args: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    command_args = _normalize_command_args(command_args)
    pkg, data = load_package(root, name)
    required_checks = ensure_required_checks(pkg, data, timestamp)
    req: dict[str, Any] | None = None
    if required_check:
        req = _required_by_id(required_checks, required_check)
        kind = kind or str(req.get("kind", "manual"))
        slice_id = slice_id or str(req.get("slice", ""))
    if not kind:
        raise ArborError("run-check requires --kind when --required-check is omitted.")
    if slice_id and not SLICE_ID_RE.match(slice_id):
        raise ArborError(f"Invalid slice id '{slice_id}'. Use S-001 format.")
    check_id = _next_check_id(data)
    cwd_text = cwd or "."
    cwd_path = Path(cwd_text)
    if not cwd_path.is_absolute():
        cwd_path = root / cwd_path
    stdout = ""
    stderr = ""
    try:
        proc = subprocess.run(command_args, cwd=cwd_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except FileNotFoundError as exc:
        exit_code = 127
        stderr = str(exc)
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr = (stderr + "\n" if stderr else "") + f"Command timed out after {timeout}s"
    status = "passed" if exit_code == 0 else "failed"
    stdout_path, stderr_path = _write_check_output(pkg, check_id, stdout, stderr)
    checks = data.setdefault("checks", [])
    if not isinstance(checks, list):
        raise ArborError("task.json checks must be a list.")
    entry: dict[str, Any] = {
        "id": check_id,
        "source": "run-check",
        "status": status,
        "kind": kind,
        "command": shlex.join(command_args),
        "cwd": cwd_text,
        "exit_code": exit_code,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "at": timestamp,
        "actor": actor,
    }
    if req is not None:
        entry["required_check"] = required_check
        entry["required_check_fingerprint"] = req.get("fingerprint")
    if slice_id:
        entry["slice"] = slice_id
    checks.append(entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "check": entry}


def _checks_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    checks = data.get("checks")
    return [item for item in checks if isinstance(item, dict)] if isinstance(checks, list) else []


def _matches_current_required(entry: dict[str, Any], req: dict[str, Any]) -> bool:
    if entry.get("required_check") != req.get("id"):
        return False
    return entry.get("required_check_fingerprint") == req.get("fingerprint")


def _latest_required_entry(checks: list[dict[str, Any]], req: dict[str, Any]) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    for entry in checks:
        if _matches_current_required(entry, req):
            latest = entry
    return latest


def _has_block_context(entry: dict[str, Any]) -> bool:
    return bool(str(entry.get("reason", "")).strip()) and bool(entry.get("evidence") or entry.get("command"))


def _automated_required(req: dict[str, Any]) -> bool:
    return bool(req.get("command_hint")) or str(req.get("kind")) in AUTOMATED_CHECK_KINDS


def _check_label(req: dict[str, Any]) -> str:
    return f"{req.get('id')} ({req.get('description')})"


def validate_slice_checks(pkg: Path, data: dict[str, Any], slice_id: str, timestamp: str) -> tuple[list[str], list[str]]:
    """Per-slice gate: every required check of this slice must have settled evidence.

    Settled means latest matching evidence passed (run-check for automated kinds),
    or latest matching evidence is blocked/not_run with concrete reason and
    evidence/command. Historical passed checks stop counting once a newer entry
    for the same current required_check exists.
    """
    required_checks = ensure_required_checks(pkg, data, timestamp)
    slice_required = [item for item in required_checks if item.get("slice") == slice_id]
    checks = _checks_list(data)
    satisfied: list[str] = []
    concerns: list[str] = []
    missing: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for req in slice_required:
        entry = _latest_required_entry(checks, req)
        if entry is None:
            missing.append(req)
            continue
        status = entry.get("status")
        if status == "passed":
            if not _automated_required(req) or entry.get("source") == "run-check":
                satisfied.append(str(entry.get("id")))
                continue
        if status in {"blocked", "not_run"} and _has_block_context(entry):
            satisfied.append(str(entry.get("id")))
            concerns.append(
                f"{req.get('id')} ({req.get('description')}): {entry.get('status')} — {str(entry.get('reason')).strip()}"
            )
            continue
        if status == "failed":
            failed.append(req)
        else:
            missing.append(req)
    if failed:
        gaps = "; ".join(_check_label(item) for item in failed)
        raise ArborError(
            f"Slice {slice_id} 不能标记 done，required checks 最新证据失败: {gaps}。"
            "出路：重新 run-check 取得 passed 证据；或确实无法执行时用 record-check --required-check <id> --status blocked|not_run "
            '--reason "<原因>" --evidence "<尝试/错误输出>" 结算为 concern。'
        )
    if missing:
        gaps = "; ".join(_check_label(item) for item in missing)
        raise ArborError(
            f"Slice {slice_id} 不能标记 done，required checks 缺结算证据: {gaps}。"
            "出路：run-check --required-check <id> -- <command> 补 passed 证据；"
            '确实无法执行用 record-check --required-check <id> --status blocked|not_run --reason "<原因>" --evidence "<尝试/错误输出>"（或 --command "<尝试命令>"）结算为 slice concern，包结果导向 done_with_concerns；'
            "slice 未完成用 mark-slice --status in_progress --note。"
        )
    deduped: list[str] = []
    for check_id in satisfied:
        if check_id not in deduped:
            deduped.append(check_id)
    return deduped, concerns


def validate_impl_checks(pkg: Path, data: dict[str, Any], state: str, check_ids: list[str], timestamp: str) -> dict[str, Any]:
    required_checks = ensure_required_checks(pkg, data, timestamp)
    if not check_ids:
        raise ArborError("Impl result DONE/DONE_WITH_CONCERNS requires --check evidence ids; free-text --command is not verification evidence.")
    checks = _checks_list(data)
    by_id = {str(item.get("id")): item for item in checks}
    unknown = [check_id for check_id in check_ids if check_id not in by_id]
    if unknown:
        raise ArborError("Impl result references unknown check ids: " + ", ".join(unknown))

    latest_by_required = {str(req.get("id")): _latest_required_entry(checks, req) for req in required_checks}
    current_by_required = {str(req.get("id")): req for req in required_checks}
    outdated: list[str] = []
    stale: list[str] = []
    referenced_latest: set[str] = set()
    for check_id in check_ids:
        entry = by_id[check_id]
        req_id = str(entry.get("required_check", ""))
        req = current_by_required.get(req_id)
        if req is None or not _matches_current_required(entry, req):
            stale.append(check_id)
            continue
        latest = latest_by_required[req_id]
        if latest is None or latest.get("id") != check_id:
            latest_id = latest.get("id") if latest else "none"
            outdated.append(f"{check_id} (latest: {latest_id})")
            continue
        referenced_latest.add(req_id)
    if stale:
        raise ArborError("Impl result references stale check evidence for changed required checks: " + ", ".join(stale))
    if outdated:
        raise ArborError("Impl result must reference latest check evidence for each required check: " + "; ".join(outdated))

    missing = [req for req in required_checks if str(req.get("id")) not in referenced_latest]
    if missing:
        raise ArborError("Impl result missing latest check evidence for required checks: " + "; ".join(_check_label(item) for item in missing))

    coverage: dict[str, dict[str, Any]] = {}
    incomplete: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for req in required_checks:
        req_id = str(req.get("id"))
        entry = latest_by_required[req_id]
        entries = [entry] if entry else []
        ok = False
        if entry is not None:
            if entry.get("status") == "passed":
                ok = (not _automated_required(req)) or entry.get("source") == "run-check"
            elif entry.get("status") in {"blocked", "not_run"} and _has_block_context(entry):
                incomplete.append(req)
            elif entry.get("status") == "failed":
                failed.append(req)
        coverage[req_id] = {
            "status": "passed" if ok else ("failed" if entry and entry.get("status") == "failed" else "incomplete"),
            "kind": req.get("kind"),
            "slice": req.get("slice"),
            "checks": [item.get("id") for item in entries if item],
        }
        if not ok and entry is not None and entry.get("status") not in {"blocked", "not_run", "failed"}:
            incomplete.append(req)
    if failed:
        raise ArborError("Impl result references failed latest check evidence for required checks: " + "; ".join(_check_label(item) for item in failed))
    if state == "done" and incomplete:
        raise ArborError("DONE requires passed check evidence for required checks: " + "; ".join(_check_label(item) for item in incomplete))
    return {"check_coverage": coverage, "incomplete_required_checks": incomplete}


def validate_functional_checks(data: dict[str, Any], state: str, check_ids: list[str]) -> dict[str, Any]:
    if not check_ids:
        raise ArborError("Impl result DONE/DONE_WITH_CONCERNS requires --functional-check evidence for final functional verification.")
    checks = _checks_list(data)
    by_id = {str(item.get("id")): item for item in checks}
    unknown = [check_id for check_id in check_ids if check_id not in by_id]
    if unknown:
        raise ArborError("Impl result references unknown functional check ids: " + ", ".join(unknown))
    referenced = [by_id[check_id] for check_id in check_ids]
    wrong_kind = [str(item.get("id")) for item in referenced if item.get("kind") != FUNCTIONAL_CHECK_KIND]
    if wrong_kind:
        raise ArborError("Functional verification must reference checks recorded with --kind functional: " + ", ".join(wrong_kind))
    latest: dict[str, Any] | None = None
    for entry in checks:
        if entry.get("kind") == FUNCTIONAL_CHECK_KIND:
            latest = entry
    if latest is None or str(latest.get("id")) not in check_ids:
        latest_id = latest.get("id") if latest else "none"
        raise ArborError(f"Impl result must reference latest functional check evidence (latest: {latest_id}).")
    if latest.get("status") == "passed":
        return {"functional_checks": check_ids, "incomplete_functional_checks": []}
    if latest.get("status") == "failed":
        raise ArborError("Functional verification latest check failed; continue implementation or record BLOCKED instead of DONE/DONE_WITH_CONCERNS.")
    if latest.get("status") in {"blocked", "not_run"} and _has_block_context(latest):
        if state == "done":
            raise ArborError("DONE requires passed functional verification evidence.")
        return {"functional_checks": check_ids, "incomplete_functional_checks": [latest]}
    raise ArborError("Functional verification latest check is incomplete; record passed evidence or blocked/not_run with --reason and --evidence/--command.")
