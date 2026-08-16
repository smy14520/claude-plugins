#!/usr/bin/env python3
"""seed — seed-kit 的最小 PRD checkbox 状态 helper。

进度模型：`.arbor/tasks/<task>/prd.md` 的 checkbox 是进度 source of truth。无 task.json，无阶段状态机。
`done-logs/` 记录机械验证（只有成功），`gate-attempts/` 记录 gate 失败留痕（熔断计数依据），
`review-loop.json` 记录显式循环终态；`impl-state.json` 是任务档案（dossier）：锚点（起点 SHA，写一次
锁死）+ 每 slice handoff + 证据指针——供任意新会话接手。以上都不是第二套进度状态。
Slice 内联在 PRD 中：`### [ ] S-NNN 标题` heading，checkbox + 内容在一起。
heading 下面的 prose（到下一个 `###` 或 `##` 为止）是 slice 内容。

gate 只卡硬事实：agent 传入的测试命令和质量命令全部 exit 0 → 翻 checkbox。
体验质量走 review-loop（loop 守好坏），不做 scoring gate 卡 done。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SLICE_HEADING_RE = re.compile(r"^### \[([ x])\] (S-\d{3})\s+(.+?)\s*$")
BAD_SLICE_HEADING_RE = re.compile(r"^###\s")
TASK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
OOS_HEADING_RE = re.compile(r"^##\s+Out of Scope\s*$")
OOS_CONFIRMED_RE = re.compile(r"[（(]用户确认[）)]")


class SeedError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- prd parsing ---------------------------------------------------------------

def tasks_root(root: Path) -> Path:
    return root / ".arbor" / "tasks"


def task_dir_path(root: Path, task: str) -> Path:
    return tasks_root(root) / task


def prd_path(root: Path, task: str) -> Path:
    return task_dir_path(root, task) / "prd.md"


@dataclass
class Slice:
    id: str
    title: str
    done: bool
    line_no: int


def _skip_html_comments(lines: list[str]) -> list[tuple[int, str]]:
    """跳过 HTML 注释块，返回 (原始行号, 行内容)。"""
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


def parse_prd(path: Path) -> tuple[list[Slice], list[str]]:
    """解析 PRD，从 `### [x] S-NNN 标题` heading 提取 slice 状态。返回 (slices, errors)。"""
    if not path.is_file():
        raise SeedError(f"未找到 {path}；先用 `seed new <task>` 创建任务")
    lines = path.read_text(encoding="utf-8").splitlines()
    slices: list[Slice] = []
    errors: list[str] = []
    seen: set[str] = set()
    in_oos = False
    for idx, line in _skip_html_comments(lines):
        stripped = line.strip()
        if stripped.startswith("## "):
            in_oos = bool(OOS_HEADING_RE.match(stripped))
            continue
        if in_oos:
            if stripped.startswith("### "):
                in_oos = False  # slice heading 开始新区段，落回正常解析
            else:
                # 排除是用户的决策：Out of Scope 顶层条目必须带（用户确认）来源标注，
                # 防止 agent 单方"不值得做"把题面声称静默排除。
                if (line.startswith("* ") or line.startswith("- ")) and not OOS_CONFIRMED_RE.search(line):
                    errors.append(
                        f"第 {idx + 1} 行：Out of Scope 条目缺少（用户确认）标注：{stripped}"
                        "——排除必须由用户拍板，确认后在条目末尾加（用户确认）"
                    )
                continue
        heading = SLICE_HEADING_RE.match(line)
        if heading:
            sl = Slice(
                id=heading.group(2), title=heading.group(3),
                done=heading.group(1) == "x", line_no=idx,
            )
            if sl.id in seen:
                errors.append(f"第 {idx + 1} 行：重复的 slice id：{sl.id}")
            else:
                seen.add(sl.id)
                slices.append(sl)
            continue
        if BAD_SLICE_HEADING_RE.match(line) and not SLICE_HEADING_RE.match(line):
            # `### something` 但不是 `### [ ] S-NNN 标题` 格式
            stripped = line.strip()
            errors.append(f"第 {idx + 1} 行：slice heading 必须是 `### [ ] S-NNN 标题`：{stripped}")
            continue
    if not slices:
        errors.append("PRD 缺少 slice heading（`### [ ] S-NNN 标题`）")
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
    raise SeedError(f"slice {slice_id} 不存在；PRD 中声明的有：{known}")


# --- done-log ----------------------------------------------------------------

def _done_log_dir(root: Path, task: str) -> Path:
    return task_dir_path(root, task) / "done-logs"


def _write_done_log(root: Path, task: str, slice_id: str, results: dict) -> Path:
    directory = _done_log_dir(root, task)
    directory.mkdir(parents=True, exist_ok=True)
    seq = len(list(directory.glob(f"*-{slice_id}.json"))) + 1
    ts = _now().replace(":", "").replace("-", "").replace("T", "-")[:15]
    filename = f"{seq:03d}-{slice_id}-{ts}.json"
    path = directory / filename
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# --- gate-attempts（gate 失败留痕）--------------------------------------------
#
# `seed done` 失败时留痕：熔断计数的唯一依据（从盘上数出来，不靠模型记忆）。
# 与 done-logs/ 分开存——done-logs 只有成功记录，seed-assert / 集成 review 重放其中的
# 命令时不会误拿失败尝试里的命令。

GATE_ATTEMPTS_DIRNAME = "gate-attempts"


def _gate_attempts_dir(root: Path, task: str) -> Path:
    return task_dir_path(root, task) / GATE_ATTEMPTS_DIRNAME


def _write_gate_attempt(root: Path, task: str, slice_id: str, payload: dict) -> Path:
    directory = _gate_attempts_dir(root, task)
    directory.mkdir(parents=True, exist_ok=True)
    seq = len(list(directory.glob(f"*-{slice_id}-*.json"))) + 1
    ts = _now().replace(":", "").replace("-", "").replace("T", "-")[:15]
    path = directory / f"{seq:03d}-{slice_id}-{ts}.json"
    payload = {**payload, "recorded_at": _now()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _count_gate_attempts(root: Path, task: str, slice_id: str) -> int:
    directory = _gate_attempts_dir(root, task)
    if not directory.is_dir():
        return 0
    return len(list(directory.glob(f"*-{slice_id}-*.json")))


# --- commands ---------------------------------------------------------------

def cmd_new(root: Path, task: str) -> int:
    if not TASK_NAME_RE.match(task):
        raise SeedError(f"任务名只允许小写字母/数字/._-：{task}")
    task_dir = task_dir_path(root, task)
    if task_dir.exists():
        raise SeedError(f"{task_dir} 已存在；用 `seed status {task}` 查看进度")
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    template = (template_dir / "prd.md").read_text(encoding="utf-8")
    task_dir.mkdir(parents=True)
    (task_dir / "notes").mkdir()
    prd_path(root, task).write_text(template.replace("{{TITLE}}", task), encoding="utf-8")
    print(f"已创建 {task_dir.relative_to(root)}/")
    print(f"下一步：填写 prd.md，然后 `seed status {task}` 校验结构")
    return 0


def _run_command(command: str, cwd: Path, timeout: int = 300) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        return -1, (exc.stdout or "") + f"\n[seed] 超时（>{timeout}s），按失败记录\n"


_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
_INLINE_INTERPRETERS = {"node", "python", "python3", "ruby", "perl", "php"}
_COMPOUND_TOKENS = {"&&", "||", ";", "|", "&", "(", ")"}


def _shell_tokens(command: str) -> list[str] | None:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return None


def _inline_program_is_noop(program: str) -> bool:
    normalized = re.sub(r"\s+", " ", program.strip()).rstrip(";").strip()
    if normalized in {"", "pass"}:
        return True
    patterns = (
        r"(?:process\.|sys\.)?exit\s*\(\s*0\s*\)",
        r"raise SystemExit(?:\s*\(\s*0\s*\))?",
        r"exit\s+0",
    )
    return any(re.fullmatch(pattern, normalized) for pattern in patterns)


def _simple_command_is_noop(parts: list[str]) -> bool:
    if not parts:
        return True
    base = Path(parts[0]).name
    if base in {"true", "false", ":", "echo", "printf"}:
        return True
    if base in _SHELLS and "-c" in parts:
        idx = parts.index("-c")
        return idx + 1 < len(parts) and _looks_like_obvious_noop(parts[idx + 1])
    if base == "exit":
        return len(parts) == 1 or parts[1:] == ["0"]
    if base in _INLINE_INTERPRETERS:
        inline_flag = next((flag for flag in ("-c", "-e", "-r") if flag in parts), None)
        if inline_flag is not None:
            idx = parts.index(inline_flag)
            return idx + 1 < len(parts) and _inline_program_is_noop(parts[idx + 1])
    return False


def _looks_like_obvious_noop(command: str) -> bool:
    """递归拒绝只由明显空操作组成的命令，不猜测真实测试工具。"""
    tokens = _shell_tokens(command.strip())
    if not tokens:
        return True

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in _COMPOUND_TOKENS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return bool(segments) and all(_simple_command_is_noop(segment) for segment in segments)


_OUTPUT_SUMMARY_LIMIT = 1000


def _command_result(command: str, exit_code: int, output: str) -> dict[str, object]:
    raw = output.encode("utf-8", errors="replace")
    clean = output.strip()
    truncated = len(clean) > _OUTPUT_SUMMARY_LIMIT
    if truncated:
        half = _OUTPUT_SUMMARY_LIMIT // 2
        summary = clean[:half] + "\n...[truncated]...\n" + clean[-half:]
    else:
        summary = clean
    return {
        "command": command,
        "exit_code": exit_code,
        "output_summary": summary,
        "output_sha256": hashlib.sha256(raw).hexdigest(),
        "output_bytes": len(raw),
        "output_truncated": truncated,
    }


def cmd_status(root: Path, task: str | None, json_output: bool) -> int:
    if task is None:
        base = tasks_root(root)
        task_dirs = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
        if not task_dirs:
            print("还没有任务；用 `seed new <task>` 创建")
            return 0
        for td in task_dirs:
            try:
                slices, errors = parse_prd(td / "prd.md")
            except SeedError as exc:
                print(f"{td.name}: 无法解析（{exc}）")
                continue
            done = sum(1 for sl in slices if sl.done)
            suffix = f"，{len(errors)} 个结构问题" if errors else ""
            print(f"{td.name}: {done}/{len(slices)} slices 完成{suffix}")
        return 0

    slices, errors = parse_prd(prd_path(root, task))
    state = _read_impl_state(root, task) or {}
    raw_dossier = state.get("slices")
    dossier = raw_dossier if isinstance(raw_dossier, dict) else {}
    reports = []
    circuit_broken: list[str] = []
    for sl in slices:
        failures = _count_gate_attempts(root, task, sl.id)
        entry = dossier.get(sl.id) if isinstance(dossier.get(sl.id), dict) else {}
        handoff = entry.get("handoff")
        reports.append({
            "id": sl.id, "title": sl.title, "done": sl.done,
            "gate_failures": failures,
            "handoff": len(handoff) if isinstance(handoff, list) else 0,
            "evidence": bool(entry.get("evidence")),
        })
        if not sl.done and failures >= CIRCUIT_BREAK_THRESHOLD:
            circuit_broken.append(sl.id)
    target = state.get("target_slice")
    scope = [sl for sl in slices if sl.id == target] if target and any(sl.id == target for sl in slices) else slices
    next_slice = next((sl.id for sl in scope if not sl.done), None)
    if json_output:
        print(json.dumps({
            "task": task,
            "task_start_sha": state.get("task_start_sha") or None,
            "target_slice": state.get("target_slice") or None,
            "slices": reports,
            "circuit_broken": circuit_broken,
            "next": next_slice,
            "errors": errors,
        }, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    for report in reports:
        mark = "x" if report["done"] else " "
        notes = []
        if report["handoff"]:
            notes.append(f"handoff {report['handoff']} 条")
        if report["evidence"]:
            notes.append("evidence ✓")
        if report["gate_failures"]:
            notes.append(f"gate 失败 {report['gate_failures']} 次")
        suffix = f"（{'，'.join(notes)}）" if notes else ""
        print(f"[{mark}] {report['id']} {report['title']}{suffix}")
    sha = state.get("task_start_sha")
    if sha:
        print(f"锚点 task_start_sha: {sha}（整体 diff：{sha}..HEAD）")
    else:
        print("无锚点（未 `impl-state init`；handoff / evidence 写入需要档案）")
    if circuit_broken:
        print(f"熔断：{', '.join(circuit_broken)} 的 gate 失败 ≥{CIRCUIT_BREAK_THRESHOLD} 次——停下报告用户；"
              f"处理后 `seed impl-state reset-attempts {task} --slice <id>` 清零再继续。")
    if errors:
        print("结构问题：")
        for err in errors:
            print(f"  - {err}")
        return 1
    if next_slice:
        print(f"next: {next_slice}")
    else:
        print("全部 slice 已完成。未声明维度仍需 review；质量没有上限。")
    return 0


def cmd_done(root: Path, task: str, slice_id: str, test_cmd: str, quality_cmds: list[str],
             evidence_files: list[str] | None = None, evidence_url: str | None = None) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)
    if sl.done:
        print(f"{slice_id} 已是完成状态")
        return 0

    if not test_cmd:
        print(f"{slice_id} 还不能标记完成——需要提供 --test 命令。", file=sys.stderr)
        print("示例: seed done <task> --slice S-001 --test \"npm test\" --quality \"npm run lint\"", file=sys.stderr)
        return 1

    if _looks_like_obvious_noop(test_cmd):
        print(f"{slice_id} 还不能标记完成——测试命令像伪装的空操作：{test_cmd}", file=sys.stderr)
        print("请传入项目真实的测试或验收命令。", file=sys.stderr)
        return 1
    for cmd in quality_cmds:
        if _looks_like_obvious_noop(cmd):
            print(f"{slice_id} 还不能标记完成——质量命令像伪装的空操作：{cmd}", file=sys.stderr)
            return 1

    results: dict[str, object] = {"test": {}, "quality": []}
    failures: list[str] = []

    # 跑测试命令
    exit_code, output = _run_command(test_cmd, root)
    results["test"] = _command_result(test_cmd, exit_code, output)
    if exit_code != 0:
        attempt = _write_gate_attempt(root, task, slice_id, {
            "slice": slice_id, "result": "fail", "failed_stage": "test", **results,
        })
        print(f"{slice_id} 还不能标记完成——测试命令未通过：", file=sys.stderr)
        print(f"  {test_cmd} → exit {exit_code}", file=sys.stderr)
        if output:
            print(f"  {output[-300:]}", file=sys.stderr)
        print(f"  失败已留痕：{attempt.relative_to(root)}", file=sys.stderr)
        return 1

    # 跑质量命令
    quality_results: list[dict[str, object]] = []
    results["quality"] = quality_results
    for cmd in quality_cmds:
        exit_code, output = _run_command(cmd, root)
        quality_results.append(_command_result(cmd, exit_code, output))
        if exit_code != 0:
            failures.append(f"质量命令失败 (exit {exit_code}): {cmd}\n{output[-500:]}")

    if failures:
        attempt = _write_gate_attempt(root, task, slice_id, {
            "slice": slice_id, "result": "fail", "failed_stage": "quality", **results,
        })
        print(f"{slice_id} 还不能标记完成——质量命令未通过：", file=sys.stderr)
        for f in failures:
            print(f"  {f[:200]}", file=sys.stderr)
        print(f"  失败已留痕：{attempt.relative_to(root)}", file=sys.stderr)
        return 1

    # 账本与证据先于 checkbox 落盘：中断最坏态 = 有证据未勾选（重跑补齐），
    # 永不出"已勾选但无证据"
    _write_done_log(root, task, slice_id, results)
    if evidence_files or evidence_url:
        _write_slice_evidence(root, task, slice_id, evidence_files or [], evidence_url)

    # 翻 checkbox：slice 头 + 该 slice 区段内的全部验收条目原子翻转，账本保持自洽
    path = prd_path(root, task)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[sl.line_no] = lines[sl.line_no].replace("### [ ]", "### [x]", 1)
    section_end = len(lines)
    for idx in range(sl.line_no + 1, len(lines)):
        stripped = lines[idx].lstrip()
        if stripped.startswith("### ") or stripped.startswith("## "):
            section_end = idx
            break
    for idx in range(sl.line_no + 1, section_end):
        stripped = lines[idx].lstrip()
        if stripped.startswith("* [ ]") or stripped.startswith("- [ ]"):
            lines[idx] = lines[idx].replace("[ ]", "[x]", 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    remaining = [other.id for other in slices if not other.done and other.id != slice_id]
    print(f"{slice_id} 已完成 ✓")
    print(f"  test: {test_cmd} → exit 0")
    for result in quality_results:
        print(f"  {result['command']}: exit {result['exit_code']}")
    print("  建议现在 commit 本 slice 的改动。")
    if remaining:
        print(f"next: {remaining[0]}")
    else:
        print("全部 slice 已完成。注意：未声明维度仍需 review；质量没有上限。")
    return 0


_VALID_VERDICTS = {"converged", "assert-stalled", "assert-unavailable", "reviewer-blind", "circuit-breaker", "rounds-exhausted"}


def cmd_review_mark(root: Path, task: str, *, verdict: str, round_num: int | None = None, note: str | None = None, depth: str = "single") -> int:
    if verdict not in _VALID_VERDICTS:
        raise SeedError(f"--verdict 必须是 {', '.join(sorted(_VALID_VERDICTS))} 之一，不允许：{verdict}")
    if round_num is not None and round_num < 1:
        raise SeedError("--round 必须 >= 1")
    task_dir = task_dir_path(root, task)
    if not task_dir.is_dir():
        raise SeedError(f"未找到 task 目录：{task}（先 `seed new {task}`）")
    if verdict == "converged":
        # 整体 review-loop 的前置是所有 slice 已过 gate；对未完成 task 写 converged
        # 会让终态与账本矛盾。硬闸在 durable state 层，绕不过去。
        slices, errors = parse_prd(prd_path(root, task))
        if errors:
            print(
                "拒绝写 converged：prd.md 结构有误，先修复：\n"
                + "\n".join(f"  - {err}" for err in errors),
                file=sys.stderr,
            )
            return 1
        unfinished = [sl.id for sl in slices if not sl.done]
        if unfinished:
            print(
                f"拒绝写 converged：task 还有未完成 slice（{', '.join(unfinished)}）。\n"
                f"先逐个 `seed done {task} --slice <id> --test \"<命令>\"` 关闭；"
                f"slice 无法用命令验证时说明它不是可交付的 slice——修 PRD（并入可验证条目或移入 Goal/Out of Scope），不要绕过 gate。",
                file=sys.stderr,
            )
            return 1
    record = {"task": task, "terminal_reason": verdict, "converged": verdict == "converged", "depth": depth}
    if round_num is not None:
        record["round"] = round_num
    if note:
        record["note"] = note
    record["written_at"] = _now()
    marker = task_dir / "review-loop.json"
    marker.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"整体 review-loop marker 已落盘：{verdict} → {marker.relative_to(root)}")
    return 0


# --- impl-state（任务档案 dossier）---------------------------------------------
#
# 没有 phase 状态机：进度 SoT 是 PRD checkbox，失败次数从 gate-attempts/ 数出来。
# impl-state.json 只存协作上下文：task 起点 SHA（写一次即锁死，中断恢复与整体 diff
# 的锚）+ 单 slice 模式目标 + 每 slice handoff + 证据指针。
# `seed status` 从 checkbox + 留痕 + 档案现算全部派生事实（next / gate 计数 / 熔断）。

IMPL_STATE_FILENAME = "impl-state.json"
CIRCUIT_BREAK_THRESHOLD = 3


def _impl_state_path(root: Path, task: str) -> Path:
    return task_dir_path(root, task) / IMPL_STATE_FILENAME


def _read_impl_state(root: Path, task: str) -> dict | None:
    p = _impl_state_path(root, task)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_impl_state(root: Path, task: str, state: dict) -> Path:
    p = _impl_state_path(root, task)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _now()
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def _require_impl_state(root: Path, task: str) -> dict:
    state = _read_impl_state(root, task)
    if state is None:
        raise SeedError(f"未找到 impl-state.json——先 `seed impl-state init {task}` 建任务档案")
    return state


def _dossier_slices(state: dict) -> dict:
    slices = state.setdefault("slices", {})
    if not isinstance(slices, dict):
        raise SeedError("impl-state.json 的 slices 字段损坏（应为对象），先人工检查档案")
    return slices


def _write_slice_evidence(root: Path, task: str, slice_id: str,
                          files: list[str], url: str | None) -> Path:
    state = _require_impl_state(root, task)
    entry = _dossier_slices(state).setdefault(slice_id, {})
    evidence = entry.setdefault("evidence", {"files": [], "artifact": {}, "commit": None})
    evidence["files"] = list(dict.fromkeys([*evidence.get("files", []), *files]))
    if url:
        evidence["artifact"] = {"url": url}
    sha, _ = _git_anchor(root)
    evidence["commit"] = sha or None
    return _write_impl_state(root, task, state)


def _normalized_prd_sha(root: Path, task: str) -> str:
    """PRD 指纹：把 slice 与条目 checkbox 归一化回未勾选再 hash——
    翻 checkbox 是工作流自己的动作，不算需求变化。"""
    prd = prd_path(root, task)
    if not prd.is_file():
        return ""
    text = re.sub(r"^### \[x\] ", "### [ ] ", prd.read_text(encoding="utf-8"), flags=re.MULTILINE)
    text = re.sub(r"^(\s*[*-]) \[x\] ", r"\1 [ ] ", text, flags=re.MULTILINE)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_anchor(root: Path) -> tuple[str, str]:
    """返回 (task_start_sha, git_root)。无 git 或无 commit 时为空字符串。
    git_root 一并记录：项目不是仓库根时（外层仓库/monorepo），锚点仍指向
    commit 实际会落入的仓库，但 init 会向用户显式提示。"""
    try:
        exit_code, top = _run_command("git rev-parse --show-toplevel", root, timeout=10)
        if exit_code != 0:
            return "", ""
        git_root = top.strip()
        exit_code, sha = _run_command("git rev-parse HEAD", root, timeout=10)
        return (sha.strip() if exit_code == 0 else ""), git_root
    except Exception:
        return "", ""


def cmd_impl_state_init(root: Path, task: str, *, target_slice: str | None = None) -> int:
    """落锚点文件。task_start_sha 写一次即锁死，之后任何 re-init 都不覆盖——
    它是中断恢复后人审 diff / revert / 集成 review 的起点。"""
    slices = _require_valid_prd(root, task)
    if target_slice is not None:
        _find_slice(slices, target_slice)
    existing = _read_impl_state(root, task) or {}
    prd_sha = _normalized_prd_sha(root, task)

    if existing.get("task_start_sha"):
        sha, git_root = existing["task_start_sha"], existing.get("git_root", "")
        locked = True
    else:
        sha, git_root = _git_anchor(root)
        locked = False

    state = {
        "task_start_sha": sha,
        "git_root": git_root,
        "target_slice": target_slice,
        "prd_sha256": prd_sha,
        "created_at": existing.get("created_at") or _now(),
        # re-init 保留已累积的 dossier（handoff/evidence）——init 只管锚点字段，
        # 清空累积数据 = 交接资产丢失
        "slices": existing.get("slices") if isinstance(existing.get("slices"), dict) else {},
    }
    p = _write_impl_state(root, task, state)

    if locked:
        print(f"impl-state 已存在，task_start_sha 保留：{sha}")
        if existing.get("prd_sha256") and existing["prd_sha256"] != prd_sha:
            print("注意：PRD 内容有变化（checkbox 翻转已归一化，不计入）——请确认需求是否被改动。")
    else:
        print(f"impl-state 锚点已落盘：{p.relative_to(root)}")
        print(f"  task_start_sha: {sha or '(非 git 仓库或无 commit；集成 review 需降级为审工作区现状)'}")
    if git_root and Path(git_root).resolve() != root.resolve():
        print(f"注意：git 仓库根是 {git_root}，不是项目根——per-slice commit 会落到该仓库，请确认。")
    if target_slice:
        print(f"  单 slice 模式：只做 {target_slice}")
    return 0


def cmd_reset_attempts(root: Path, task: str, *, slice_id: str) -> int:
    """熔断后由用户显式清零：把该 slice 的失败留痕移入 superseded/（历史保留，计数归零）。"""
    slices = _require_valid_prd(root, task)
    _find_slice(slices, slice_id)
    directory = _gate_attempts_dir(root, task)
    files = sorted(directory.glob(f"*-{slice_id}-*.json")) if directory.is_dir() else []
    if not files:
        print(f"{slice_id} 没有失败留痕，无需清零。")
        return 0
    superseded = directory / "superseded"
    superseded.mkdir(exist_ok=True)
    stamp = _now().replace(":", "").replace("-", "").replace("T", "-")[:15]
    for f in files:
        f.rename(superseded / f"{stamp}-{f.name}")
    print(f"{slice_id} 的 {len(files)} 条失败留痕已移入 {superseded.relative_to(root)}/，计数归零。")
    return 0


def cmd_handoff_add(root: Path, task: str, slice_id: str, note: str) -> int:
    """追加 slice handoff 到任务档案。只收代码与 git 读不出的隐性事实。"""
    slices = _require_valid_prd(root, task)
    _find_slice(slices, slice_id)
    if not note.strip():
        raise SeedError("--note 不能为空")
    state = _require_impl_state(root, task)
    entry = _dossier_slices(state).setdefault(slice_id, {})
    handoff = entry.setdefault("handoff", [])
    handoff.append(note.strip())
    p = _write_impl_state(root, task, state)
    print(f"{slice_id} handoff 已记录（第 {len(handoff)} 条）→ {p.relative_to(root)}")
    return 0


def _project_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _load_json_object(root: Path, value: str, label: str) -> tuple[Path, dict]:
    path = _project_path(root, value)
    if not path.is_file():
        raise SeedError(f"{label} 指向的 JSON 文件不存在：{value}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SeedError(f"{label} 不是合法 JSON：{value}（{exc.msg}）") from exc
    if not isinstance(data, dict):
        raise SeedError(f"{label} 必须是 JSON object：{value}")
    return path, data


def _score_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SeedError(f"{field} 必须是数字")
    return float(value)


def cmd_score_aggregate(root: Path, rubric_path: str, score_files: list[str], out_path: str) -> int:
    try:
        _, rubric = _load_json_object(root, rubric_path, "--rubric")
        dimensions = rubric.get("dimensions", {})
        if not isinstance(dimensions, dict) or not dimensions:
            raise SeedError("rubric 必须包含非空 object 字段 dimensions")
        all_scores = []
        for sf_path in score_files:
            _, score_doc = _load_json_object(root, sf_path, f"--score-files ({sf_path})")
            all_scores.append(score_doc)
        if not all_scores:
            raise SeedError("至少需要一个 score-file")
        aggregated = {}
        for dim_name in dimensions:
            score_values = []
            judge_scores = {}
            for i, sf in enumerate(all_scores):
                scores = sf.get("scores", {})
                if not isinstance(scores, dict):
                    raise SeedError(f"score-file ({score_files[i]}) 的 scores 字段必须是 object")
                if dim_name not in scores:
                    continue
                raw = scores[dim_name]
                if isinstance(raw, dict):
                    value = _score_number(raw.get("score", 0), f"score-file ({score_files[i]}).scores.{dim_name}.score")
                else:
                    value = _score_number(raw, f"score-file ({score_files[i]}).scores.{dim_name}")
                score_values.append(value)
                judge_scores[f"judge-{i+1}"] = value
            if not score_values:
                raise SeedError(f"维度 {dim_name} 在所有 score-file 中都不存在")
            sorted_vals = sorted(score_values)
            n = len(sorted_vals)
            median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2 if n % 2 == 0 else sorted_vals[n // 2]
            aggregated[dim_name] = {
                "score": median, "judge_scores": judge_scores,
                "range": max(score_values) - min(score_values),
                "min": min(score_values), "max": max(score_values),
            }
        total = sum(d["score"] for d in aggregated.values())
        average = total / len(aggregated) if aggregated else 0.0
        output = {
            "rubric_id": rubric.get("id"), "method": "median",
            "judges": [f"judge-{i+1}" for i in range(len(all_scores))],
            "dimensions": aggregated, "average": average, "source_files": score_files,
        }
        out_full = _project_path(root, out_path)
        out_full.parent.mkdir(parents=True, exist_ok=True)
        out_full.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"聚合完成：{len(all_scores)} 个裁判，{len(aggregated)} 个维度，average={average:.2f}")
        return 0
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1


# --- map（wayfinder 决策图 helper）--------------------------------------------
#
# .arbor/maps/<slug>/：map.md（五节索引，散文）+ tickets/（决策票，frontmatter 记状态）。
# helper 只做确定性动作：new 脚手架、status 从票 frontmatter 推导 frontier 并做结构校验。
# 收票（写 Resolution / 翻 status）是 agent 的语义动作，helper 保持只读——map 子命令族无其他写操作。
# 票不进 gate、不翻 PRD checkbox：决策账本与交付账本严格分离。

MAP_DIRNAME = "maps"
RESOLUTION_HEADING_RE = re.compile(r"^##\s+Resolution\s*$", re.MULTILINE)


def maps_root(root: Path) -> Path:
    return root / ".arbor" / MAP_DIRNAME


def map_dir_path(root: Path, slug: str) -> Path:
    return maps_root(root) / slug


@dataclass
class Ticket:
    id: str
    path: Path
    status: str
    blocked_by: list[str]
    has_resolution: bool


def _parse_frontmatter(text: str) -> dict[str, str]:
    """解析 `---` 围起来的 frontmatter（扁平 key: value 子集，不引第三方依赖）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped in ("---", "..."):
            break
        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        fields[key.strip()] = value.strip()
    return fields


def _split_refs(raw: str) -> list[str]:
    """blocked-by 值 → 票号列表；兼容 `a`、`a, b`、`[a, b]` 三种写法。"""
    value = raw.strip().strip("[]")
    if not value:
        return []
    refs: list[str] = []
    for token in re.split(r"[,;\s]+", value):
        token = token.strip().strip("\"'")
        if token:
            refs.append(token)
    return refs


def _load_tickets(tickets_dir: Path) -> tuple[list[Ticket], list[str]]:
    """读 tickets/*.md → (tickets, errors)。票号 = frontmatter id（缺省用文件名 stem）。"""
    tickets: list[Ticket] = []
    errors: list[str] = []
    if not tickets_dir.is_dir():
        return tickets, errors
    seen: dict[str, Path] = {}
    for path in sorted(tickets_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fields = _parse_frontmatter(text)
        if "status" not in fields:
            errors.append(f"{path.name}：缺少 frontmatter（--- 围起的 type/status 块）或 status 字段")
            continue
        ticket_id = fields.get("id", "").strip().strip("\"'") or path.stem
        if ticket_id in seen:
            errors.append(f"票号重复：{ticket_id}（{seen[ticket_id].name} 与 {path.name}）")
            continue
        seen[ticket_id] = path
        blocked_raw = fields.get("blocked-by") or fields.get("blocked_by") or ""
        tickets.append(Ticket(
            id=ticket_id,
            path=path,
            status=fields["status"].strip().strip("\"'"),
            blocked_by=_split_refs(blocked_raw),
            has_resolution=bool(RESOLUTION_HEADING_RE.search(text)),
        ))
    return tickets, errors


def _validate_tickets(tickets: list[Ticket], errors: list[str]) -> list[str]:
    """结构校验：status 枚举、blocked-by 引用存在、closed 票必有 ## Resolution（票号唯一在加载时查）。"""
    known = {t.id for t in tickets}
    for t in tickets:
        if t.status not in ("open", "closed"):
            errors.append(f"{t.path.name}：status 必须是 open 或 closed，当前：{t.status or '(空)'}")
        for ref in t.blocked_by:
            if ref not in known:
                errors.append(f"{t.path.name}：blocked-by 引用了不存在的票：{ref}")
        if t.status == "closed" and not t.has_resolution:
            errors.append(f"{t.path.name}：closed 票缺少 `## Resolution` 节")
    return errors


def cmd_map_new(root: Path, slug: str) -> int:
    if not TASK_NAME_RE.match(slug):
        raise SeedError(f"图名只允许小写字母/数字/._-：{slug}")
    map_dir = map_dir_path(root, slug)
    if map_dir.exists():
        raise SeedError(f"{map_dir} 已存在；用 `seed map status {slug}` 查看图状态")
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    template = (template_dir / "map.md").read_text(encoding="utf-8")
    (map_dir / "tickets").mkdir(parents=True)
    (map_dir / "map.md").write_text(template.replace("{{SLUG}}", slug), encoding="utf-8")
    print(f"已创建 {map_dir.relative_to(root)}/（map.md + tickets/）")
    print(f"下一步：拍 Destination，把能立住的问题写进 tickets/，然后 `seed map status {slug}` 看 frontier")
    return 0


def cmd_map_status(root: Path, slug: str, json_output: bool) -> int:
    map_dir = map_dir_path(root, slug)
    if not map_dir.is_dir():
        raise SeedError(f"未找到 {map_dir}；先用 `seed map new {slug}` 开图")
    tickets, errors = _load_tickets(map_dir / "tickets")
    _validate_tickets(tickets, errors)
    closed_ids = {t.id for t in tickets if t.status == "closed"}
    open_ids = [t.id for t in tickets if t.status == "open"]
    frontier = [
        t.id for t in tickets
        if t.status == "open" and all(ref in closed_ids for ref in t.blocked_by)
    ]
    if json_output:
        # 只输出从票 frontmatter 推导的事实；map.md 散文节（Not yet specified 等）不进 JSON
        print(json.dumps({
            "map": slug,
            "tickets": {"open": len(open_ids), "closed": len(closed_ids), "total": len(tickets)},
            "frontier": frontier,
            "errors": errors,
        }, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    print(f"open {len(open_ids)} / closed {len(closed_ids)} / 共 {len(tickets)} 张票")
    print(f"frontier：{', '.join(frontier) if frontier else '空'}")
    if errors:
        print("结构问题：")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


# --- entry ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seed",
        description="seed-kit helper：prd.md checkbox 记进度；done 跑项目测试+质量命令，全过翻 checkbox并写验证记录。",
    )
    parser.add_argument("--root", default=".", help="项目根目录（含 .arbor/）")
    sub = parser.add_subparsers(dest="command", required=True)

    new_parser = sub.add_parser("new", help="脚手架 .arbor/tasks/<task>/prd.md")
    new_parser.add_argument("task")

    status_parser = sub.add_parser("status", help="解析 PRD 的 slice heading：进度、下一个 slice")
    status_parser.add_argument("task", nargs="?")
    status_parser.add_argument("--json", dest="json_output", action="store_true")

    done_parser = sub.add_parser("done", help="跑项目测试+质量命令，全过则勾选 slice checkbox")
    done_parser.add_argument("task")
    done_parser.add_argument("--slice", dest="slice_id", required=True)
    done_parser.add_argument("--test", dest="test_cmd", default="", help="测试命令（如 'npm test'）")
    done_parser.add_argument("--quality", dest="quality_cmds", action="append", default=[], help="质量命令，可重复多次")
    done_parser.add_argument("--evidence-file", dest="evidence_files", action="append", default=[], metavar="PATH",
                             help="证据文件指针（截图等），可重复；写入 impl-state.json 档案对应 slice")
    done_parser.add_argument("--evidence-url", dest="evidence_url", default=None,
                             help="验收实例锚点 URL；写入 impl-state.json 档案对应 slice")

    rm_parser = sub.add_parser("review-mark", help="落显式 task 级 review-loop 终态 marker")
    rm_parser.add_argument("task")
    rm_parser.add_argument("--verdict", required=True)
    rm_parser.add_argument("--round", dest="round_num", type=int, default=None)
    rm_parser.add_argument("--note", default=None)
    rm_parser.add_argument("--depth", choices=["inline", "single", "full"], default="single",
                           help="审查深度：inline=编排者内联自查（impl 默认收尾）；single=派过 1 个 review agent；full=5 agent review-loop（增强项）")

    # 任务档案（dossier）
    impl_state_parser = sub.add_parser("impl-state", help="任务档案：锚点（起点 SHA 写一次锁死）/ 单 slice 目标 / 熔断清零")
    impl_sub = impl_state_parser.add_subparsers(dest="impl_state_cmd", required=True)
    impl_init = impl_sub.add_parser("init", help="落锚点文件（task_start_sha 写一次即锁死）")
    impl_init.add_argument("task")
    impl_init.add_argument("--slice", dest="target_slice", default=None, help="单 slice 模式的目标 slice")
    impl_reset = impl_sub.add_parser("reset-attempts", help="熔断后清零某 slice 的 gate 失败计数（留痕移入 superseded/）")
    impl_reset.add_argument("task")
    impl_reset.add_argument("--slice", dest="slice_id", required=True)

    handoff_parser = sub.add_parser("handoff", help="任务档案：写入 slice 交接（handoff）")
    handoff_sub = handoff_parser.add_subparsers(dest="handoff_cmd", required=True)
    handoff_add = handoff_sub.add_parser("add", help="追加一条 slice handoff（代码与 git 读不出的隐性事实）")
    handoff_add.add_argument("task")
    handoff_add.add_argument("--slice", dest="slice_id", required=True)
    handoff_add.add_argument("--note", required=True)


    score_parser = sub.add_parser("score", help="评分聚合（review-loop judge 多裁判模式用）")
    score_sub = score_parser.add_subparsers(dest="score_cmd", required=True)
    agg_parser = score_sub.add_parser("aggregate", help="聚合多个 score-file（多裁判模式）")
    agg_parser.add_argument("--rubric", required=True, help="rubric JSON 路径")
    agg_parser.add_argument("--score-files", nargs="+", required=True, help="score-file JSON 路径列表")
    agg_parser.add_argument("--out", required=True, help="输出聚合结果路径")

    map_new_parser = sub.add_parser("map", help="wayfinder 决策图（.arbor/maps/<slug>/）")
    map_sub = map_new_parser.add_subparsers(dest="map_cmd", required=True)
    map_new = map_sub.add_parser("new", help="脚手架 .arbor/maps/<slug>/（map.md + tickets/）")
    map_new.add_argument("slug")
    map_status = map_sub.add_parser("status", help="从票 frontmatter 推导 open/closed 与 frontier（只读）")
    map_status.add_argument("slug")
    map_status.add_argument("--json", dest="json_output", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["wiki"]:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from wiki import main as wiki_main
        return wiki_main(argv[1:])
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "new":
            return cmd_new(root, args.task)
        if args.command == "status":
            return cmd_status(root, args.task, args.json_output)
        if args.command == "done":
            return cmd_done(root, args.task, args.slice_id, args.test_cmd, args.quality_cmds,
                            evidence_files=args.evidence_files, evidence_url=args.evidence_url)
        if args.command == "review-mark":
            return cmd_review_mark(root, args.task, verdict=args.verdict, round_num=args.round_num, note=args.note, depth=args.depth)
        if args.command == "impl-state":
            if args.impl_state_cmd == "init":
                return cmd_impl_state_init(root, args.task, target_slice=args.target_slice)
            if args.impl_state_cmd == "reset-attempts":
                return cmd_reset_attempts(root, args.task, slice_id=args.slice_id)
        if args.command == "handoff":
            if args.handoff_cmd == "add":
                return cmd_handoff_add(root, args.task, slice_id=args.slice_id, note=args.note)
        if args.command == "score":
            if args.score_cmd == "aggregate":
                return cmd_score_aggregate(root, args.rubric, args.score_files, args.out)
        if args.command == "map":
            if args.map_cmd == "new":
                return cmd_map_new(root, args.slug)
            if args.map_cmd == "status":
                return cmd_map_status(root, args.slug, args.json_output)
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
