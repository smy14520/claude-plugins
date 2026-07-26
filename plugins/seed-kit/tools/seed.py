#!/usr/bin/env python3
"""seed — seed-kit 的最小 PRD checkbox 状态 helper。

进度模型：`.arbor/tasks/<task>/prd.md` 的 checkbox 是进度 source of truth。无 task.json，无阶段状态机。
`done-logs/` 记录机械验证（只有成功），`gate-attempts/` 记录 gate 失败留痕（impl-agent 熔断计数依据），
`review-loop.json` 记录显式循环终态，`impl-state.json` 是 impl-agent 的任务锚点（起点 SHA / 单 slice 目标）；
以上都不是第二套进度状态。
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
    for idx, line in _skip_html_comments(lines):
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
# `seed done` 失败时留痕：impl-agent 熔断计数的唯一依据（从盘上数出来，不靠模型记忆）。
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
    reports = [{"id": sl.id, "title": sl.title, "done": sl.done} for sl in slices]
    next_slice = next((sl.id for sl in slices if not sl.done), None)
    if json_output:
        print(json.dumps({
            "task": task, "slices": reports, "errors": errors, "next": next_slice,
        }, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    for report in reports:
        mark = "x" if report["done"] else " "
        print(f"[{mark}] {report['id']} {report['title']}")
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


def cmd_done(root: Path, task: str, slice_id: str, test_cmd: str, quality_cmds: list[str]) -> int:
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

    # 翻 checkbox
    path = prd_path(root, task)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[sl.line_no] = lines[sl.line_no].replace("### [ ]", "### [x]", 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _write_done_log(root, task, slice_id, results)

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


def cmd_review_mark(root: Path, task: str, *, verdict: str, round_num: int | None = None, note: str | None = None) -> int:
    if verdict not in _VALID_VERDICTS:
        raise SeedError(f"--verdict 必须是 {', '.join(sorted(_VALID_VERDICTS))} 之一，不允许：{verdict}")
    if round_num is not None and round_num < 1:
        raise SeedError("--round 必须 >= 1")
    task_dir = task_dir_path(root, task)
    if not task_dir.is_dir():
        raise SeedError(f"未找到 task 目录：{task}（先 `seed new {task}`）")
    record = {"task": task, "terminal_reason": verdict, "converged": verdict == "converged"}
    if round_num is not None:
        record["round"] = round_num
    if note:
        record["note"] = note
    record["written_at"] = _now()
    marker = task_dir / "review-loop.json"
    marker.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"整体 review-loop marker 已落盘：{verdict} → {marker.relative_to(root)}")
    return 0


# --- impl-state（impl-agent 编排锚点 + 纯推导 next-action）--------------------
#
# 没有 phase 状态机：进度 SoT 是 PRD checkbox，失败次数从 gate-attempts/ 数出来，
# impl-state.json 只存推导不出来的两样东西——task 起点 SHA（写一次即锁死，中断恢复
# 的锚）和单 slice 模式的目标 slice。next-action 只读机器事实，不记录模型自报状态。
# 只在 impl-agent 模式启用；impl 单 agent 模式忽略。

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


def _normalized_prd_sha(root: Path, task: str) -> str:
    """PRD 指纹：把 slice checkbox 归一化回未勾选再 hash——
    翻 checkbox 是工作流自己的动作，不算需求变化。"""
    prd = prd_path(root, task)
    if not prd.is_file():
        return ""
    text = re.sub(r"^### \[x\] ", "### [ ] ", prd.read_text(encoding="utf-8"), flags=re.MULTILINE)
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


def _standards_list(root: Path) -> list[str]:
    standards = [name for name in ("CLAUDE.md", "DESIGN.md") if (root / name).is_file()]
    rules_dir = root / ".claude" / "rules"
    if rules_dir.is_dir():
        standards.extend(sorted(p.name for p in rules_dir.iterdir() if p.is_file()))
    return standards


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
        "standards": _standards_list(root),
        "created_at": existing.get("created_at") or _now(),
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


def cmd_next_action(root: Path, task: str) -> int:
    """编排驱动：只读机器事实（PRD checkbox + gate-attempts 失败留痕 + 锚点）→ 输出现在该干嘛。

    不写任何状态。下一个 slice、熔断、收口时机全部从盘上推导，不依赖模型自报。"""
    slices, errors = parse_prd(prd_path(root, task))
    if errors:
        print(json.dumps({"error": "PRD 结构问题", "details": errors},
                         ensure_ascii=False), file=sys.stderr)
        return 1

    state = _read_impl_state(root, task)
    done_count = sum(1 for sl in slices if sl.done)

    if state is None:
        # 无锚点 = 未入场。若有未完成 slice → 建议 init
        next_slice = next((sl.id for sl in slices if not sl.done), None)
        if next_slice is None:
            print(json.dumps({"action": "noop", "reason": "all slices done, no impl-state"},
                             ensure_ascii=False))
            return 0
        print(json.dumps({"action": "init_impl_state", "next_slice": next_slice},
                         ensure_ascii=False))
        return 0

    target = state.get("target_slice")
    if target:
        scope = [sl for sl in slices if sl.id == target]
        if not scope:
            print(json.dumps({"error": f"target_slice {target} 不在 PRD 中"},
                             ensure_ascii=False), file=sys.stderr)
            return 1
    else:
        scope = slices
    next_slice = next((sl.id for sl in scope if not sl.done), None)

    out: dict[str, object] = {
        "next_slice": next_slice,
        "attempt_count": _count_gate_attempts(root, task, next_slice) if next_slice else 0,
        "done_count": done_count,
        "total_slices": len(slices),
        "task_start_sha": state.get("task_start_sha", ""),
    }
    if target:
        out["target_slice"] = target

    attempt_count = out["attempt_count"]
    if next_slice is None:
        if target:
            out["action"] = "finish"
            out["note"] = f"单 slice 模式：{target} 已过 gate。per-slice review + commit 后即收，不做集成 review。"
        else:
            sha = state.get("task_start_sha", "")
            out["action"] = "integration_review"
            out["dispatch"] = "集成 review（主会话审 committed diff；修不净再手动 review-loop 深兜底）"
            out["diff_range"] = f"{sha}..HEAD" if sha else None
            if not sha:
                out["note"] = "无 task_start_sha（非 git 项目）：降级为审工作区现状并如实说明，不发明 diff 范围。"
    elif attempt_count >= CIRCUIT_BREAK_THRESHOLD:
        out["action"] = "escalate"
        out["hint"] = (
            f"{next_slice} 的 gate 已失败 {attempt_count} 次（≥{CIRCUIT_BREAK_THRESHOLD}，熔断）：停下报告用户。"
            f"用户处理后用 `seed impl-state reset-attempts {task} --slice {next_slice}` 清零计数再继续。"
        )
    else:
        out["action"] = "start_slice"
        dispatch = f"seed-slice agent for {next_slice}"
        if done_count:
            dispatch += "（注入 handoff）"
        if attempt_count:
            dispatch += f"——第 {attempt_count + 1} 次尝试，把 gate-attempts/ 里的失败输出一并注入"
        out["dispatch"] = dispatch

    print(json.dumps(out, ensure_ascii=False, indent=2))
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

    rm_parser = sub.add_parser("review-mark", help="落显式 task 级 review-loop 终态 marker")
    rm_parser.add_argument("task")
    rm_parser.add_argument("--verdict", required=True)
    rm_parser.add_argument("--round", dest="round_num", type=int, default=None)
    rm_parser.add_argument("--note", default=None)

    # impl-agent 编排锚点（plumbing，只在 impl-agent 模式用）
    impl_state_parser = sub.add_parser("impl-state", help="impl-agent 编排锚点（起点 SHA / 单 slice 目标 / 失败计数清零）")
    impl_sub = impl_state_parser.add_subparsers(dest="impl_state_cmd", required=True)
    impl_init = impl_sub.add_parser("init", help="落锚点文件（task_start_sha 写一次即锁死）")
    impl_init.add_argument("task")
    impl_init.add_argument("--slice", dest="target_slice", default=None, help="单 slice 模式的目标 slice")
    impl_show = impl_sub.add_parser("show", help="查看当前锚点")
    impl_show.add_argument("task")
    impl_reset = impl_sub.add_parser("reset-attempts", help="熔断后清零某 slice 的 gate 失败计数（留痕移入 superseded/）")
    impl_reset.add_argument("task")
    impl_reset.add_argument("--slice", dest="slice_id", required=True)

    na_parser = sub.add_parser("next-action", help="impl-agent 编排驱动：读 checkbox+失败留痕+锚点 → 现在该干嘛（只读）")
    na_parser.add_argument("task")

    score_parser = sub.add_parser("score", help="评分聚合（review-loop judge 多裁判模式用）")
    score_sub = score_parser.add_subparsers(dest="score_cmd", required=True)
    agg_parser = score_sub.add_parser("aggregate", help="聚合多个 score-file（多裁判模式）")
    agg_parser.add_argument("--rubric", required=True, help="rubric JSON 路径")
    agg_parser.add_argument("--score-files", nargs="+", required=True, help="score-file JSON 路径列表")
    agg_parser.add_argument("--out", required=True, help="输出聚合结果路径")

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
            return cmd_done(root, args.task, args.slice_id, args.test_cmd, args.quality_cmds)
        if args.command == "review-mark":
            return cmd_review_mark(root, args.task, verdict=args.verdict, round_num=args.round_num, note=args.note)
        if args.command == "impl-state":
            if args.impl_state_cmd == "init":
                return cmd_impl_state_init(root, args.task, target_slice=args.target_slice)
            if args.impl_state_cmd == "show":
                state = _read_impl_state(root, args.task)
                if state is None:
                    print(json.dumps({"status": "no impl-state（未入场）"}, ensure_ascii=False))
                else:
                    print(json.dumps(state, ensure_ascii=False, indent=2))
                return 0
            if args.impl_state_cmd == "reset-attempts":
                return cmd_reset_attempts(root, args.task, slice_id=args.slice_id)
        if args.command == "next-action":
            return cmd_next_action(root, args.task)
        if args.command == "score":
            if args.score_cmd == "aggregate":
                return cmd_score_aggregate(root, args.rubric, args.score_files, args.out)
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
