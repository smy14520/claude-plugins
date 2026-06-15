#!/usr/bin/env python3
"""seed — minimal PRD-checkbox state helper for seed-kit.

State model: `.seed/tasks/<task>/prd.md` slice checkboxes + `evidence/` are the
only durable state. No task.json, no state machine. Single ownership: the
`## Slices` section in prd.md is an ordered checkbox index (one line per
slice); each slice's acceptance + verification items live only in
`slices/S-NNN.md`.

Verification has three kinds — the closed vocabulary for "what makes passed
trustworthy, and who/what asserts it":

- `assert`  — an executable command that genuinely asserts (it must exit
  non-zero on failure: a test suite, a contract replay, a Playwright spec).
  Gate: exit_code == 0 → passed. A bare probe (`curl` without `--fail`, `echo`)
  only proves "it ran", not "it is correct"; seed flags such shapes as a
  *smoke warning* (soft, never blocks) — real verification needs an asserting
  command.
- `judge`  — assessed by an independent agent (生成者 ≠ 验证者) against an
  AC rubric, in a fresh session. Gate: a recorded verdict == pass. The helper
  only records/validates the verdict; the judging itself is a skill-layer
  action (the helper never calls an LLM).
- `human`  — genuine stakeholder sign-off (taste, compliance, things that by
  definition can't be automated). Gate: a recorded sign-off with note + who.

Legacy forms keep working: a bare `` `command` `` item is `assert`; a
`[manual]` item is `human`.

The single hard gate: `seed done` flips a slice checkbox only when every
verification item declared in the slice file has recorded evidence of the
right shape for its kind (assert: passed; judge: pass verdict; human: sign-off).
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
SLICE_FILE_H1_RE = re.compile(r"^# (S-\d{3})\s+(.+?)\s*$")
ACCEPT_HEADING_RE = re.compile(r"^## (?:验收|Acceptance)")
VERIFY_HEADING_RE = re.compile(r"^## (?:验证|Verification)")
COMMAND_ITEM_RE = re.compile(r"^`(.+)`$")
MANUAL_ITEM_RE = re.compile(r"^\[manual\]\s*(.+)$")
KIND_PREFIX_RE = re.compile(r"^\[(assert|judge|human)\]\s*(.*)$", re.DOTALL)
SLICES_SECTION = "## Slices"

# On-disk evidence `kind` aliases for back-compat with records written before
# the three-kind vocabulary existed.
KIND_ALIASES = {"automated": "assert", "manual": "human"}

# Commands that "exit 0 no matter what the feature did" — flagged as smoke.
SMOKE_TOOL_RE = re.compile(r"(?:^|[\s|&;])(curl|wget)(?:[\s|&;]|$)")


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


def _has_fail_flag(command: str) -> bool:
    """curl/wget --fail (or -f, including clustered like -sf) present."""
    for tok in command.split():
        if tok == "--fail" or tok.startswith("--fail="):
            return True
        if tok.startswith("-") and not tok.startswith("--") and "f" in tok:
            return True
    return False


def looks_like_smoke(command: str) -> tuple[bool, str]:
    """High-precision smoke heuristic: True only for shapes that exit 0
    regardless of correctness. Conservative — false negatives are fine, false
    positives are not."""
    if not command.strip():
        return False, ""
    first = command.strip().split()[0]
    # bare curl/wget with no --fail and no pipe/chain to an asserting tool
    if SMOKE_TOOL_RE.search(command):
        if _has_fail_flag(command):
            return False, ""
        if any(op in command for op in ("|", "&&", "||")):
            return False, ""
        return True, "curl/wget 无 --fail 且无管道/链式断言：只证路由可达，不证语义正确"
    # echo / true / : with no downstream assertion
    if first in ("echo", "true", ":") and not any(op in command for op in ("|", "&&", "||")):
        return True, f"裸 `{first}` 不是断言：只证明命令执行了"
    return False, ""


def classify_check(item: str) -> tuple[str, str] | None:
    r"""Classify a verification list-item into (kind, target) or None.

    Recognizes [assert] <cmd>, [judge] desc, [human] desc, a legacy bare
    backticked command (-> assert), and legacy [manual] desc (-> human)."""
    prefixed = KIND_PREFIX_RE.match(item)
    if prefixed:
        kind, rest = prefixed.group(1), prefixed.group(2).strip()
        if not rest:
            return None
        if kind == "assert":
            cmd = COMMAND_ITEM_RE.match(rest)
            return ("assert", normalize_command(cmd.group(1))) if cmd else None
        return (kind, normalize_text(rest))
    cmd = COMMAND_ITEM_RE.match(item)
    if cmd:
        return ("assert", normalize_command(cmd.group(1)))
    manual = MANUAL_ITEM_RE.match(item)
    if manual:
        return ("human", normalize_text(manual.group(1)))
    return None


@dataclass
class Check:
    kind: str  # "assert" | "judge" | "human"
    target: str  # normalized command (assert) or text (judge/human)
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
    """Parse the `## Slices` checkbox index in prd.md plus each slices/S-NNN.md.

    prd.md owns order + status (one `### [ ] S-NNN 标题` line per slice);
    slices/S-NNN.md owns acceptance + verification items. Nothing is stated twice.
    Returns (slices, structural errors).
    """
    if not path.is_file():
        raise SeedError(f"未找到 {path}；先用 `seed new <task>` 创建任务")
    lines = path.read_text(encoding="utf-8").splitlines()
    slices: list[Slice] = []
    errors: list[str] = []
    in_slices = False
    for idx, line in _content_lines(lines):
        stripped = line.strip()
        if line.startswith("## "):
            in_slices = stripped == SLICES_SECTION
            continue
        if not in_slices or not stripped:
            continue
        heading = SLICE_HEADING_RE.match(line)
        if heading:
            slices.append(
                Slice(
                    id=heading.group(2),
                    title=heading.group(3),
                    done=heading.group(1) == "x",
                    line_no=idx,
                )
            )
            continue
        if BAD_SLICE_HEADING_RE.match(line):
            errors.append(f"第 {idx + 1} 行：slice 索引行必须是 `### [ ] S-NNN 标题`：{stripped}")
            continue
        errors.append(
            f"第 {idx + 1} 行：`## Slices` 只放索引行，slice 内容写在 slices/S-NNN.md：{stripped}"
        )
    if not slices:
        errors.append("prd.md 缺少 `## Slices` 或其中没有任何 slice")
    seen: set[str] = set()
    for sl in slices:
        if sl.id in seen:
            errors.append(f"重复的 slice id：{sl.id}")
        seen.add(sl.id)
        errors.extend(_load_slice_file(path.parent / "slices", sl))
    return slices, errors


def _content_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Drop HTML comment blocks; return (original index, line) for the rest."""
    out: list[tuple[int, str]] = []
    in_comment = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        out.append((idx, line))
    return out


def _load_slice_file(slices_dir: Path, sl: Slice) -> list[str]:
    """Parse slices/S-NNN.md into sl.checks. Returns structural errors."""
    rel = f"slices/{sl.id}.md"
    file_path = slices_dir / f"{sl.id}.md"
    if not file_path.is_file():
        return [f"缺少 {rel}：slice 的验收与验证项住在这个文件里"]
    errors: list[str] = []
    content = _content_lines(file_path.read_text(encoding="utf-8").splitlines())
    body = [(idx, line) for idx, line in content if line.strip()]
    if not body:
        return [f"{rel} 是空的"]
    h1 = SLICE_FILE_H1_RE.match(body[0][1])
    if not h1:
        errors.append(f"{rel} 第一行必须是 `# {sl.id} 标题`")
    else:
        if h1.group(1) != sl.id:
            errors.append(f"{rel} 标题 id（{h1.group(1)}）与文件名不符")
        if normalize_text(h1.group(2)) != normalize_text(sl.title):
            errors.append(f"{rel} 标题与 prd.md 索引行不一致：{h1.group(2)!r} ≠ {sl.title!r}")
    has_accept = False
    in_verify = False
    for idx, line in content:
        stripped = line.strip()
        if line.startswith("## "):
            has_accept = has_accept or bool(ACCEPT_HEADING_RE.match(stripped))
            in_verify = bool(VERIFY_HEADING_RE.match(stripped))
            continue
        if not in_verify or not stripped:
            continue
        if not stripped.startswith(("- ", "* ")):
            errors.append(f"{rel} `## 验证` 下第 {idx + 1} 行不是 `- ` 列表项：{stripped}")
            continue
        item = stripped[2:].strip()
        classified = classify_check(item)
        if classified:
            kind, target = classified
            sl.checks.append(Check(kind, target, item))
        else:
            errors.append(
                f"{rel} 验证项无法识别（需为 `[assert] \\`命令\\`` / `[judge] 描述` / "
                f"`[human] 描述`，或旧式 `\\`命令\\`` / `[manual] 描述`）：{item}"
            )
    if not has_accept:
        errors.append(f"{rel} 缺少 `## 验收` 段")
    if not sl.checks:
        errors.append(f"{rel} 缺少验证项：`## 验证` 至少声明一条 `[assert] \\`命令\\`` / `[judge]` / `[human]`")
    return errors


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


def _record_kind(record: dict) -> str:
    return KIND_ALIASES.get(record.get("kind"), record.get("kind"))


def expected_state(kind: str) -> str:
    if kind == "human":
        return "recorded"
    return "passed"  # assert and judge both gate on a passing result


def check_state(check: Check, records: list[dict]) -> str:
    """passed | failed | recorded | missing — based on the latest matching record."""
    state = "missing"
    for record in records:
        rk = _record_kind(record)
        if check.kind == "assert":
            if rk == "assert" and record.get("command") == check.target:
                state = "passed" if record.get("exit_code") == 0 else "failed"
        elif check.kind == "judge":
            if rk == "judge" and record.get("item") == check.target:
                verdict = record.get("verdict")
                if verdict == "pass":
                    state = "passed"
                elif verdict == "fail":
                    state = "failed"
        else:  # human
            if rk == "human" and record.get("item") == check.target and record.get("note"):
                state = "recorded"
    return state


# --- commands ---------------------------------------------------------------

def cmd_new(root: Path, task: str) -> int:
    if not TASK_NAME_RE.match(task):
        raise SeedError(f"任务名只允许小写字母/数字/._-：{task}")
    task_dir = task_dir_path(root, task)
    if task_dir.exists():
        raise SeedError(f"{task_dir} 已存在；用 `seed status {task}` 查看进度")
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    template = (template_dir / "prd.md").read_text(encoding="utf-8")
    (task_dir / "evidence").mkdir(parents=True)
    (task_dir / "notes").mkdir()
    (task_dir / "slices").mkdir()
    prd_path(root, task).write_text(template.replace("{{TITLE}}", task), encoding="utf-8")
    slice_template = (template_dir / "slice.md").read_text(encoding="utf-8")
    (task_dir / "slices" / "S-001.md").write_text(slice_template, encoding="utf-8")
    print(f"已创建 {task_dir.relative_to(root)}/")
    print(f"下一步：填写 prd.md 与 slices/S-NNN.md，然后 `seed status {task}` 校验结构")
    return 0


def _slice_report(root: Path, task: str, sl: Slice) -> dict:
    records = load_evidence(root, task, sl.id)
    checks = []
    for check in sl.checks:
        entry = {"kind": check.kind, "target": check.target, "state": check_state(check, records)}
        if check.kind == "assert":
            smoke, _ = looks_like_smoke(check.target)
            if smoke:
                entry["smoke"] = True
        checks.append(entry)
    return {
        "id": sl.id,
        "title": sl.title,
        "done": sl.done,
        "file": f"slices/{sl.id}.md",
        "checks": checks,
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
            if check.get("smoke"):
                print("        ⚠ 疑似烟雾测试（只证可达/可执行，不证语义）；建议改成会失败的断言或换 [judge]/[human]")
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
    *,
    mode: str,
    manual_item: str | None,
    judge_item: str | None,
    verdict: str | None,
    grade: str | None,
    trace: str | None,
    note: str | None,
    evidence: str | None,
    by: str | None,
    timeout: int,
) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)

    if mode == "judge":
        item = normalize_text(judge_item or "")
        declared = [c for c in sl.checks if c.kind == "judge" and c.target == item]
        if not declared:
            options = [c.target for c in sl.checks if c.kind == "judge"] or ["（无）"]
            raise SeedError(
                f"{slice_id} 未声明这条 judge 验证项；slices/{slice_id}.md 中声明的 judge 项：\n"
                + "\n".join(f"  - {opt}" for opt in options)
            )
        if verdict not in ("pass", "fail"):
            raise SeedError("judge 记录必须带 --verdict pass|fail")
        if not trace:
            raise SeedError("judge 记录必须带 --trace（裁判依据/证据指针，例如 rubric 文件 + 截图/输出位置）")
        record = {
            "slice": slice_id,
            "kind": "judge",
            "item": item,
            "verdict": verdict,
            "trace": trace,
            "status": "passed" if verdict == "pass" else "failed",
            "by": by or "independent-judge",
            "created_at": _now(),
        }
        if grade:
            record["grade"] = grade
        if note:
            record["note"] = note
        path = _write_evidence(root, task, slice_id, record, None)
        print(f"{record['status']} (verdict={verdict}) → {path.relative_to(root)}")
        return 0 if verdict == "pass" else 1

    if mode == "human":
        item = normalize_text(manual_item or "")
        declared = [c for c in sl.checks if c.kind == "human" and c.target == item]
        if not declared:
            options = [c.target for c in sl.checks if c.kind == "human"] or ["（无）"]
            raise SeedError(
                f"{slice_id} 未声明这条 human 验证项（[manual] 视为 [human]）；"
                f"slices/{slice_id}.md 中声明的 human 项：\n"
                + "\n".join(f"  - {opt}" for opt in options)
            )
        if not note:
            raise SeedError("human 记录必须带 --note（验证了什么、结论）")
        record = {
            "slice": slice_id,
            "kind": "human",
            "item": item,
            "note": note,
            "by": by or "user",
            "status": "recorded",
            "created_at": _now(),
        }
        if evidence:
            record["evidence"] = evidence
        path = _write_evidence(root, task, slice_id, record, None)
        print(f"recorded → {path.relative_to(root)}")
        return 0

    # assert
    if not cmd_tokens:
        raise SeedError("缺少要执行的命令：seed run-check <task> --slice S-NNN -- <command>")
    command = normalize_command(shlex.join(cmd_tokens))
    declared = [c for c in sl.checks if c.kind == "assert" and c.target == command]
    if not declared:
        options = [c.target for c in sl.checks if c.kind == "assert"] or ["（无）"]
        raise SeedError(
            f"{slice_id} 未声明这条验证命令（命令必须与 slices/{slice_id}.md 声明一致，不接受替代/弱化命令）；声明的命令：\n"
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
        "kind": "assert",
        "command": command,
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "created_at": _now(),
    }
    smoke, reason = looks_like_smoke(command)
    path = _write_evidence(root, task, slice_id, record, output)
    print(f"{record['status']} (exit {exit_code}) → {path.relative_to(root)}")
    if smoke and exit_code == 0:
        print(f"⚠ 烟雾警告：{reason}。这条命令即使功能错误也会 exit 0，不构成有效验证。", file=sys.stderr)
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
        if state != expected_state(check.kind):
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

    new_parser = sub.add_parser("new", help="脚手架 .seed/tasks/<task>/：prd.md 模板 + slices/S-001.md")
    new_parser.add_argument("task")

    status_parser = sub.add_parser("status", help="解析 prd.md 索引与 slices/：进度、证据状态、结构校验、下一个 slice")
    status_parser.add_argument("task", nargs="?")
    status_parser.add_argument("--json", dest="json_output", action="store_true")

    rc_parser = sub.add_parser(
        "run-check",
        help="assert：执行 slices/S-NNN.md 声明的命令并落盘证据；judge/human：记录裁决/签收",
    )
    rc_parser.add_argument("task")
    rc_parser.add_argument("--slice", dest="slice_id", required=True)
    rc_parser.add_argument("--judge", help="[judge] 验证项原文（由独立 agent 在 fresh session 裁决后记录）")
    rc_parser.add_argument("--verdict", choices=["pass", "fail"], help="judge：裁决结果")
    rc_parser.add_argument("--grade", help="judge：评分/等级（可选）")
    rc_parser.add_argument("--trace", help="judge：裁决依据/证据指针（rubric + 截图/输出位置）")
    rc_parser.add_argument("--human", help="[human] 验证项原文")
    rc_parser.add_argument("--manual", help="[manual] 验证项原文（旧式，等同 --human）")
    rc_parser.add_argument("--note", help="human/judge：验证了什么、结论")
    rc_parser.add_argument("--evidence", help="human：证据指针（截图路径/输出位置，可选）")
    rc_parser.add_argument("--by", help="human/judge：签收人/裁决者（默认 user / independent-judge）")
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
            if args.judge is not None:
                mode, manual_item, judge_item = "judge", None, args.judge
            elif args.manual is not None or args.human is not None:
                mode, manual_item, judge_item = "human", (args.manual or args.human), None
            else:
                mode, manual_item, judge_item = "assert", None, None
            return cmd_run_check(
                root,
                args.task,
                args.slice_id,
                cmd_tokens,
                mode=mode,
                manual_item=manual_item,
                judge_item=judge_item,
                verdict=args.verdict,
                grade=args.grade,
                trace=args.trace,
                note=args.note,
                evidence=args.evidence,
                by=args.by,
                timeout=args.timeout,
            )
        if args.command == "done":
            return cmd_done(root, args.task, args.slice_id)
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
