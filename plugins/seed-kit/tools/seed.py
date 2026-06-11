#!/usr/bin/env python3
"""seed — minimal PRD-checkbox state helper for seed-kit.

State model: `.seed/tasks/<task>/prd.md` slice checkboxes + `evidence/` are the
only durable state. No task.json, no state machine. The single hard gate:
`seed done` flips a slice checkbox only when every verification item declared
in the PRD has recorded evidence (automated: a real passed run with exit_code 0;
manual: a record with note + evidence pointer).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SLICE_HEADING_RE = re.compile(r"^### \[([ x])\] (S-\d{3})\s+(.+?)\s*$")
BAD_SLICE_HEADING_RE = re.compile(r"^###\s")
TASK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
VERIFY_LABEL_RE = re.compile(r"^-\s*(?:验证|Verification)\s*[:：]\s*$")
COMMAND_ITEM_RE = re.compile(r"^`(.+)`$")
MANUAL_ITEM_RE = re.compile(r"^\[manual\]\s*(.+)$")
SLICES_SECTION = "## Slices"


class SeedError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_command(command: str) -> str:
    try:
        return shlex.join(shlex.split(command))
    except ValueError:
        return " ".join(command.split())


def normalize_text(text: str) -> str:
    return " ".join(text.split())


@dataclass
class Check:
    kind: str  # "automated" | "manual"
    target: str  # normalized command, or normalized manual item text
    raw: str


@dataclass
class Slice:
    id: str
    title: str
    done: bool
    line_no: int  # 0-based line index of the heading in prd.md
    checks: list[Check] = field(default_factory=list)


def tasks_root(root: Path) -> Path:
    return root / ".seed" / "tasks"


def task_dir_path(root: Path, task: str) -> Path:
    return tasks_root(root) / task


def prd_path(root: Path, task: str) -> Path:
    return task_dir_path(root, task) / "prd.md"


def parse_prd(path: Path) -> tuple[list[Slice], list[str]]:
    """Parse `## Slices` out of prd.md. Returns (slices, structural errors)."""
    if not path.is_file():
        raise SeedError(f"未找到 {path}；先用 `seed new <task>` 创建任务")
    lines = path.read_text(encoding="utf-8").splitlines()
    slices: list[Slice] = []
    errors: list[str] = []
    in_slices = False
    current: Slice | None = None
    in_verify = False
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            in_slices = line.strip() == SLICES_SECTION
            current = None
            in_verify = False
            continue
        if not in_slices:
            continue
        heading = SLICE_HEADING_RE.match(line)
        if heading:
            current = Slice(
                id=heading.group(2),
                title=heading.group(3),
                done=heading.group(1) == "x",
                line_no=idx,
            )
            slices.append(current)
            in_verify = False
            continue
        if BAD_SLICE_HEADING_RE.match(line):
            errors.append(f"第 {idx + 1} 行：slice 标题必须是 `### [ ] S-NNN 标题`：{line.strip()}")
            current = None
            in_verify = False
            continue
        if current is None:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip(" "))
        if stripped.startswith("- ") and indent == 0:
            in_verify = bool(VERIFY_LABEL_RE.match(stripped))
            continue
        if in_verify and stripped.startswith("- ") and indent > 0:
            item = stripped[2:].strip()
            cmd = COMMAND_ITEM_RE.match(item)
            manual = MANUAL_ITEM_RE.match(item)
            if cmd:
                current.checks.append(Check("automated", normalize_command(cmd.group(1)), item))
            elif manual:
                current.checks.append(Check("manual", normalize_text(manual.group(1)), item))
            else:
                errors.append(f"{current.id} 验证项无法识别（需为 `命令` 或 [manual] 描述）：{item}")
    if not slices:
        errors.append("prd.md 缺少 `## Slices` 或其中没有任何 slice")
    seen: set[str] = set()
    for sl in slices:
        if sl.id in seen:
            errors.append(f"重复的 slice id：{sl.id}")
        seen.add(sl.id)
        if not sl.checks:
            errors.append(f"{sl.id} 缺少验证项：每个 slice 必须声明至少一条 `命令` 或 [manual] 验证")
    return slices, errors


def _require_valid_prd(root: Path, task: str) -> list[Slice]:
    slices, errors = parse_prd(prd_path(root, task))
    if errors:
        raise SeedError("prd.md 结构有误，先修复：\n" + "\n".join(f"  - {err}" for err in errors))
    return slices


def _find_slice(slices: list[Slice], slice_id: str) -> Slice:
    for sl in slices:
        if sl.id == slice_id:
            return sl
    known = ", ".join(sl.id for sl in slices)
    raise SeedError(f"slice {slice_id} 不存在；prd.md 中声明的有：{known}")


# --- evidence ---------------------------------------------------------------

def evidence_dir(root: Path, task: str, slice_id: str) -> Path:
    return task_dir_path(root, task) / "evidence" / slice_id


def load_evidence(root: Path, task: str, slice_id: str) -> list[dict]:
    directory = evidence_dir(root, task, slice_id)
    records: list[dict] = []
    if not directory.is_dir():
        return records
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


def _write_evidence(root: Path, task: str, slice_id: str, record: dict, log_text: str | None) -> Path:
    directory = evidence_dir(root, task, slice_id)
    directory.mkdir(parents=True, exist_ok=True)
    seq = len(list(directory.glob("*.json"))) + 1
    stem = f"{seq:03d}-{record['kind']}"
    if log_text is not None:
        log_path = directory / f"{stem}.log"
        log_path.write_text(log_text, encoding="utf-8")
        record["log"] = log_path.name
    json_path = directory / f"{stem}.json"
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_path


def check_state(check: Check, records: list[dict]) -> str:
    """passed | failed | recorded | missing — based on the latest matching record."""
    state = "missing"
    for record in records:
        if check.kind == "automated":
            if record.get("kind") == "automated" and record.get("command") == check.target:
                state = "passed" if record.get("exit_code") == 0 else "failed"
        else:
            if (
                record.get("kind") == "manual"
                and record.get("item") == check.target
                and record.get("note")
                and record.get("evidence")
            ):
                state = "recorded"
    return state


# --- commands ---------------------------------------------------------------

def cmd_new(root: Path, task: str) -> int:
    if not TASK_NAME_RE.match(task):
        raise SeedError(f"任务名只允许小写字母/数字/._-：{task}")
    task_dir = task_dir_path(root, task)
    if task_dir.exists():
        raise SeedError(f"{task_dir} 已存在；用 `seed status {task}` 查看进度")
    template_path = Path(__file__).resolve().parent.parent / "templates" / "prd.md"
    template = template_path.read_text(encoding="utf-8")
    (task_dir / "evidence").mkdir(parents=True)
    (task_dir / "notes").mkdir()
    prd_path(root, task).write_text(template.replace("{{TITLE}}", task), encoding="utf-8")
    print(f"已创建 {task_dir.relative_to(root)}/")
    print(f"下一步：填写 prd.md，然后 `seed status {task}` 校验结构")
    return 0


def _slice_report(root: Path, task: str, sl: Slice) -> dict:
    records = load_evidence(root, task, sl.id)
    return {
        "id": sl.id,
        "title": sl.title,
        "done": sl.done,
        "checks": [
            {"kind": check.kind, "target": check.target, "state": check_state(check, records)}
            for check in sl.checks
        ],
    }


def cmd_status(root: Path, task: str | None, json_output: bool) -> int:
    if task is None:
        base = tasks_root(root)
        task_dirs = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
        if not task_dirs:
            print("还没有任务；用 `seed new <task>` 创建")
            return 0
        for task_dir in task_dirs:
            try:
                slices, errors = parse_prd(task_dir / "prd.md")
            except SeedError as exc:
                print(f"{task_dir.name}: 无法解析（{exc}）")
                continue
            done = sum(1 for sl in slices if sl.done)
            suffix = f"，{len(errors)} 个结构问题" if errors else ""
            print(f"{task_dir.name}: {done}/{len(slices)} slices 完成{suffix}")
        return 0

    slices, errors = parse_prd(prd_path(root, task))
    reports = [_slice_report(root, task, sl) for sl in slices]
    next_slice = next((sl.id for sl in slices if not sl.done), None)
    if json_output:
        print(
            json.dumps(
                {"task": task, "slices": reports, "errors": errors, "next": next_slice},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if errors else 0
    for report in reports:
        mark = "x" if report["done"] else " "
        print(f"[{mark}] {report['id']} {report['title']}")
        for check in report["checks"]:
            print(f"      {check['state']:<8} [{check['kind']}] {check['target']}")
    if errors:
        print("结构问题：")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"next: {next_slice}" if next_slice else "全部 slice 已完成")
    return 0


def cmd_run_check(
    root: Path,
    task: str,
    slice_id: str,
    cmd_tokens: list[str],
    manual: str | None,
    note: str | None,
    evidence: str | None,
    timeout: int,
) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)

    if manual is not None:
        item = normalize_text(manual)
        declared = [c for c in sl.checks if c.kind == "manual" and c.target == item]
        if not declared:
            options = [c.target for c in sl.checks if c.kind == "manual"] or ["（无）"]
            raise SeedError(
                f"{slice_id} 未声明这条 manual 验证项；PRD 中声明的 manual 项：\n"
                + "\n".join(f"  - {opt}" for opt in options)
            )
        if not note or not evidence:
            raise SeedError("manual 记录必须同时带 --note（验证了什么、结论）和 --evidence（截图路径/输出位置等证据指针）")
        record = {
            "slice": slice_id,
            "kind": "manual",
            "item": item,
            "note": note,
            "evidence": evidence,
            "status": "recorded",
            "created_at": _now(),
        }
        path = _write_evidence(root, task, slice_id, record, None)
        print(f"recorded → {path.relative_to(root)}")
        return 0

    if not cmd_tokens:
        raise SeedError("缺少要执行的命令：seed run-check <task> --slice S-NNN -- <command>")
    command = normalize_command(shlex.join(cmd_tokens))
    declared = [c for c in sl.checks if c.kind == "automated" and c.target == command]
    if not declared:
        options = [c.target for c in sl.checks if c.kind == "automated"] or ["（无）"]
        raise SeedError(
            f"{slice_id} 未声明这条验证命令（命令必须与 PRD 声明一致，不接受替代/弱化命令）；声明的命令：\n"
            + "\n".join(f"  - {opt}" for opt in options)
        )
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        output = proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        exit_code = -1
        output = (exc.stdout or "") + f"\n[seed] 超时（>{timeout}s），按失败记录\n"
    record = {
        "slice": slice_id,
        "kind": "automated",
        "command": command,
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "created_at": _now(),
    }
    path = _write_evidence(root, task, slice_id, record, output)
    print(f"{record['status']} (exit {exit_code}) → {path.relative_to(root)}")
    return 0 if exit_code == 0 else 1


def cmd_done(root: Path, task: str, slice_id: str) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)
    if sl.done:
        print(f"{slice_id} 已是完成状态")
        return 0
    records = load_evidence(root, task, slice_id)
    gaps: list[str] = []
    for check in sl.checks:
        state = check_state(check, records)
        expected = "recorded" if check.kind == "manual" else "passed"
        if state != expected:
            gaps.append(f"[{check.kind}] {check.target} → {state}")
    if gaps:
        print(f"{slice_id} 还不能标记完成，缺少证据：", file=sys.stderr)
        for gap in gaps:
            print(f"  - {gap}", file=sys.stderr)
        print("用 `seed run-check` 补齐后重试。", file=sys.stderr)
        return 1
    path = prd_path(root, task)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[sl.line_no] = lines[sl.line_no].replace("### [ ]", "### [x]", 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    remaining = [other.id for other in slices if not other.done and other.id != slice_id]
    print(f"{slice_id} 已完成 ✓  建议现在 commit 本 slice 的改动。")
    print(f"next: {remaining[0]}" if remaining else "全部 slice 已完成，可以触发 review。")
    return 0


# --- entry ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seed",
        description="seed-kit helper：prd.md checkbox + evidence 是唯一状态；done 只认 run-check 落盘的证据。",
    )
    parser.add_argument("--root", default=".", help="项目根目录（含 .seed/）")
    sub = parser.add_subparsers(dest="command", required=True)

    new_parser = sub.add_parser("new", help="脚手架 .seed/tasks/<task>/ 与 prd.md 模板")
    new_parser.add_argument("task")

    status_parser = sub.add_parser("status", help="解析 prd.md：进度、证据状态、结构校验、下一个 slice")
    status_parser.add_argument("task", nargs="?")
    status_parser.add_argument("--json", dest="json_output", action="store_true")

    rc_parser = sub.add_parser(
        "run-check",
        help="真实执行 PRD 声明的验证命令并落盘证据；或 --manual 记录人工验证",
    )
    rc_parser.add_argument("task")
    rc_parser.add_argument("--slice", dest="slice_id", required=True)
    rc_parser.add_argument("--manual", help="PRD 中声明的 [manual] 验证项原文")
    rc_parser.add_argument("--note", help="manual：验证了什么、结论")
    rc_parser.add_argument("--evidence", help="manual：证据指针（截图路径/输出位置）")
    rc_parser.add_argument("--timeout", type=int, default=600)

    done_parser = sub.add_parser("done", help="证据齐备后勾选 slice checkbox（唯一合法勾选入口）")
    done_parser.add_argument("task")
    done_parser.add_argument("--slice", dest="slice_id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["wiki"]:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from wiki import main as wiki_main

        return wiki_main(argv[1:])
    cmd_tokens: list[str] = []
    if "--" in argv:
        split_at = argv.index("--")
        cmd_tokens = argv[split_at + 1 :]
        argv = argv[:split_at]
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "new":
            return cmd_new(root, args.task)
        if args.command == "status":
            return cmd_status(root, args.task, args.json_output)
        if args.command == "run-check":
            return cmd_run_check(
                root,
                args.task,
                args.slice_id,
                cmd_tokens,
                args.manual,
                args.note,
                args.evidence,
                args.timeout,
            )
        if args.command == "done":
            return cmd_done(root, args.task, args.slice_id)
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
