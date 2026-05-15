from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .prd_slices import parse_prd_slices
from .schema import SLICE_ID_RE

CHECK_STATUSES = {"passed", "failed", "blocked", "not_run"}
AUTOMATED_CHECK_KINDS = {"build", "test", "typecheck", "lint", "docker", "api"}

_VERIFICATION_HEADING_RE = re.compile(r"^##+\s+Verification\s*$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^##+\s+")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_CHECK_ID_RE = re.compile(r"^chk_(\d{3})$")


def _slice_files(pkg: Path) -> list[Path]:
    slices_dir = pkg / "slices"
    if not slices_dir.exists():
        return []
    return sorted(path for path in slices_dir.glob("S-*.md") if SLICE_ID_RE.match(path.stem))


def _verification_items(text: str) -> list[str]:
    items: list[str] = []
    in_verification = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if _HEADING_RE.match(line):
            if in_verification:
                break
            in_verification = bool(_VERIFICATION_HEADING_RE.match(line))
            continue
        if not in_verification:
            continue
        if line.startswith("- "):
            item = line[2:].strip()
            if item:
                items.append(item)
    return items


def _command_hint(description: str) -> str | None:
    match = _BACKTICK_RE.search(description)
    if not match:
        return None
    return match.group(1).strip() or None


def _infer_kind(description: str, command_hint: str | None) -> str:
    text = f"{description} {command_hint or ''}".lower()
    if "docker" in text or "compose" in text or "container" in text or "容器" in text:
        return "docker"
    if "typecheck" in text or "type check" in text or "tsc" in text or "类型" in text:
        return "typecheck"
    if "lint" in text:
        return "lint"
    if "test" in text or "pytest" in text or "php artisan test" in text or "vitest" in text or "测试" in text:
        return "test"
    if "build" in text or "构建" in text or "编译" in text:
        return "build"
    if "curl" in text or "/api/" in text or " api" in text or "http " in text or "http 200" in text:
        return "api"
    if "browser" in text or "页面" in text or "ui" in text or "点击" in text or "可访问" in text:
        return "browser"
    return "manual"


def _required_check_id(slice_id: str, index: int) -> str:
    return f"req_{slice_id.replace('-', '')}_{index:03d}"


def _derive_required_checks_from_pkg(pkg: Path) -> list[dict[str, Any]]:
    required: list[dict[str, Any]] = []
    for slice_file in _slice_files(pkg):
        slice_id = slice_file.stem
        text = slice_file.read_text(encoding="utf-8")
        for index, item in enumerate(_verification_items(text), start=1):
            command_hint = _command_hint(item)
            check: dict[str, Any] = {
                "id": _required_check_id(slice_id, index),
                "slice": slice_id,
                "kind": _infer_kind(item, command_hint),
                "description": item,
                "required": True,
                "source": f"slices/{slice_file.name}#Verification",
            }
            if command_hint:
                check["command_hint"] = command_hint
            required.append(check)
    if required:
        return required

    prd_path = pkg / "prd.md"
    if prd_path.exists():
        slices, errors = parse_prd_slices(prd_path.read_text(encoding="utf-8"))
        if errors:
            raise ArborError("Cannot read PRD slices for required checks: " + "; ".join(errors))
        for item in slices:
            for index, test in enumerate(getattr(item, "tests", []), start=1):
                command_hint = test.strip()
                check = {
                    "id": _required_check_id(item.id, index),
                    "slice": item.id,
                    "kind": _infer_kind(command_hint, command_hint),
                    "description": command_hint,
                    "required": True,
                    "source": "prd.md#Slices",
                    "command_hint": command_hint,
                }
                required.append(check)
    if not required:
        raise ArborError("No required checks found. Add ## Verification bullets to slice task files before recording DONE.")
    return required


def ensure_required_checks(pkg: Path, data: dict[str, Any], timestamp: str) -> list[dict[str, Any]]:
    existing = data.get("required_checks")
    if isinstance(existing, list) and existing:
        return existing
    required = _derive_required_checks_from_pkg(pkg)
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
    if required_check:
        entry["required_check"] = required_check
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
    if required_check:
        entry["required_check"] = required_check
    if slice_id:
        entry["slice"] = slice_id
    checks.append(entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "check": entry}


def validate_impl_checks(pkg: Path, data: dict[str, Any], state: str, check_ids: list[str], timestamp: str) -> dict[str, Any]:
    required_checks = ensure_required_checks(pkg, data, timestamp)
    if not check_ids:
        raise ArborError("Impl result DONE/DONE_WITH_CONCERNS requires --check evidence ids; free-text --command is not verification evidence.")
    checks = data.get("checks")
    if not isinstance(checks, list):
        raise ArborError("task.json checks must be a list before recording impl result.")
    by_id = {str(item.get("id")): item for item in checks if isinstance(item, dict)}
    unknown = [check_id for check_id in check_ids if check_id not in by_id]
    if unknown:
        raise ArborError("Impl result references unknown check ids: " + ", ".join(unknown))
    by_required: dict[str, list[dict[str, Any]]] = {str(item.get("id")): [] for item in required_checks}
    for check_id in check_ids:
        entry = by_id[check_id]
        req_id = entry.get("required_check")
        if req_id in by_required:
            by_required[str(req_id)].append(entry)
    missing = [req for req in required_checks if not by_required[str(req.get("id"))]]
    if missing:
        raise ArborError("Impl result missing check evidence for required checks: " + "; ".join(f"{item.get('id')} ({item.get('description')})" for item in missing))
    coverage: dict[str, dict[str, Any]] = {}
    incomplete: list[dict[str, Any]] = []
    for req in required_checks:
        req_id = str(req.get("id"))
        entries = by_required[req_id]
        automated = bool(req.get("command_hint")) or str(req.get("kind")) in AUTOMATED_CHECK_KINDS
        passed_entries = [entry for entry in entries if entry.get("status") == "passed"]
        if automated:
            ok = any(entry.get("source") == "run-check" for entry in passed_entries)
        else:
            ok = bool(passed_entries)
        coverage[req_id] = {
            "status": "passed" if ok else "incomplete",
            "kind": req.get("kind"),
            "slice": req.get("slice"),
            "checks": [entry.get("id") for entry in entries],
        }
        if not ok:
            incomplete.append(req)
    if state == "done" and incomplete:
        raise ArborError("DONE requires passed check evidence for required checks: " + "; ".join(f"{item.get('id')} ({item.get('description')})" for item in incomplete))
    return {"check_coverage": coverage, "incomplete_required_checks": incomplete}
