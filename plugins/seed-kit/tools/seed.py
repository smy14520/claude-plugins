#!/usr/bin/env python3
"""seed — minimal PRD-checkbox state helper for seed-kit.

State model: `.arbor/tasks/<task>/prd.md` slice checkboxes + `evidence/` are the
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
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SLICE_HEADING_RE = re.compile(r"^### \[([ x])\] (S-\d{3})\s+(.+?)\s*$")
BAD_SLICE_HEADING_RE = re.compile(r"^###\s")
TASK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SLICE_FILE_H1_RE = re.compile(r"^# (S-\d{3})\s+(.+?)\s*$")
ACCEPT_HEADING_RE = re.compile(r"^## (?:验收|Acceptance)")
DELIVERY_HEADING_RE = re.compile(r"^## (?:交付面|Delivery Surfaces?)")
VERIFY_HEADING_RE = re.compile(r"^## (?:验证|验证面|Verification|Verification Surfaces?)")
COMMAND_ITEM_RE = re.compile(r"^`(.+)`$")
COMMAND_IN_REST_RE = re.compile(r"^`([^`]+)`")  # legacy：[assert] 命令在行首 backtick 内，尾部注释忽略
OBLIGATION_RE = re.compile(r"^\s*([^:`][^:]*?)\s*:\s*(.+)$", re.DOTALL)  # 新格式：<obligation-id>: <可观测行为>
MANUAL_ITEM_RE = re.compile(r"^\[manual\]\s*(.+)$")
KIND_PREFIX_RE = re.compile(
    r"^\[(assert|judge|human)\](?:\s*\[([a-z0-9._-]+(?:\s*,\s*[a-z0-9._-]+)*)\])?\s*(.*)$",
    re.DOTALL,
)
SLICES_SECTION = "## Slices"
# 参考词汇表（非封闭）：常见 Web 产品的交付面示例。项目可用任意面名（游戏 gameplay、CLI cli-dx、
# 数据管道 data-quality 等）——helper 只校验"声明的交付面被验证项覆盖"（集合关系，面名字无关），
# 不限定面名，也不规定"该面该什么 kind"（交项目 .claude/rules + review）。
SUGGESTED_SURFACES = ("backend-domain", "api", "web-ui", "e2e", "compliance", "infra")

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
    # Collapse whitespace only. Do NOT round-trip through shlex — it would
    # re-quote shell metacharacters (parens, &&, |) and break their execution.
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


def _suggested_surfaces() -> str:
    return ", ".join(SUGGESTED_SURFACES)


def _parse_surface_list(raw: str | None) -> tuple[list[str], str | None]:
    # 交付面是项目自由标签——只去重 + 非空，不校验名字（面名该是什么由项目定）。
    if raw is None:
        return [], None
    seen: set[str] = set()
    out: list[str] = []
    for surface in (part.strip() for part in raw.split(",")):
        if not surface:
            continue
        if surface in seen:
            return [], f"重复验证面：{surface}"
        seen.add(surface)
        out.append(surface)
    return out, None


def _surface_coverage_error(check: Check, surface: str) -> str | None:
    if surface not in check.surfaces:
        return "验证项未标注该交付面"
    # 仅 legacy assert（命令在 target、obligation_id=None）parse 期能判 smoke；
    # 新格式 obligation assert 的命令在 run-check 时才绑定，parse 期跳过（run-check 期硬挡）。
    # 不按面名规定 kind——"该面该用 assert/judge/human"是项目标准（写 .claude/rules），交 review 查"验证降级"。
    if check.kind == "assert" and check.obligation_id is None and looks_like_smoke(check.target)[0]:
        return "smoke assert 只证可达/可执行，不覆盖交付面"
    return None


def _coverage_requirement(surface: str) -> str:
    return f"{surface} 需要至少一条非烟雾的验证项覆盖（该面该用 assert/judge/human 由项目标准定，见 .claude/rules）"


def classify_check(item: str) -> tuple[str, str | None, list[str], str | None]:
    r"""Classify a verification list-item.

    Returns one of:
      (kind, target, surfaces, obligation_id) — recognized check (kind ∈ assert/judge/human)
      ("doc", None, [], None)      — documentation line, skip silently
      ("broken", msg, [], None)    — malformed kind-tagged item or surface tag

    A prefixed item (`[kind][surface] <rest>`) takes two forms:
      obligation: `<obligation-id>: <可观测行为>` (colon-separated; id 不以 backtick 开头)
                  → obligation_id = id, target = 行为描述。命令不在 slice，run-check 时按
                    `--obligation <id>` 绑定。
      legacy:     assert 行首 backtick `命令`，或 judge/human 纯文本描述
                  → obligation_id = None, target = 命令 / 文本。
    `assert` 需要命令或 obligation；`judge`/`human` 也接受纯文本描述作 legacy fallback。
    """
    prefixed = KIND_PREFIX_RE.match(item)
    if prefixed:
        kind, surface_raw, rest = prefixed.group(1), prefixed.group(2), prefixed.group(3).strip()
        surfaces, surface_error = _parse_surface_list(surface_raw)
        if surface_error:
            return ("broken", surface_error, [], None)
        obl = OBLIGATION_RE.match(rest)
        if obl:
            oid = normalize_text(obl.group(1))
            behavior = normalize_text(obl.group(2))
            if oid and behavior:
                return (kind, behavior, surfaces, oid)
            return ("broken", f"声明了 [{kind}] 的 obligation 不完整（需要 `<id>: <行为>`）", [], None)
        if kind == "assert":
            cmd = COMMAND_IN_REST_RE.match(rest)
            if cmd:
                return ("assert", normalize_command(cmd.group(1)), surfaces, None)
            return ("broken", "声明了 [assert] 但没有 `<obligation-id>: <行为>` 或 backtick 命令", [], None)
        if rest:
            return (kind, normalize_text(rest), surfaces, None)
        return ("broken", f"声明了 [{kind}] 但没有描述", [], None)
    cmd = COMMAND_ITEM_RE.match(item)
    if cmd:
        return ("assert", normalize_command(cmd.group(1)), [], None)
    manual = MANUAL_ITEM_RE.match(item)
    if manual:
        return ("human", normalize_text(manual.group(1)), [], None)
    return ("doc", None, [], None)


@dataclass
class Check:
    kind: str  # "assert" | "judge" | "human"
    target: str  # 新格式：可观测行为；legacy：normalized 命令 (assert) 或文本 (judge/human)
    raw: str
    surfaces: list[str] = field(default_factory=list)
    obligation_id: str | None = None  # 新格式 `<id>: <行为>` 的 id；legacy 为 None


@dataclass
class Slice:
    id: str
    title: str
    done: bool
    line_no: int  # 0-based line index of the heading in prd.md
    delivery_surfaces: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)


def tasks_root(root: Path) -> Path:
    return root / ".arbor" / "tasks"


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
    """Parse slices/S-NNN.md into delivery surfaces + checks. Returns structural errors."""
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
    has_delivery = False
    in_delivery = False
    in_verify = False
    delivery_base_indent = None
    verify_base_indent = None
    delivery_seen: set[str] = set()
    for idx, line in content:
        stripped = line.strip()
        if line.startswith("## "):
            has_accept = has_accept or bool(ACCEPT_HEADING_RE.match(stripped))
            in_delivery = bool(DELIVERY_HEADING_RE.match(stripped))
            in_verify = bool(VERIFY_HEADING_RE.match(stripped))
            has_delivery = has_delivery or in_delivery
            delivery_base_indent = None
            verify_base_indent = None
            continue
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        is_list = stripped.startswith(("- ", "* "))
        if in_delivery:
            if delivery_base_indent is None and is_list:
                delivery_base_indent = indent
            if not is_list or (delivery_base_indent is not None and indent > delivery_base_indent):
                continue
            surface = normalize_text(stripped[2:].strip())
            if not surface:
                errors.append(f"{rel} 交付面不能为空")
            elif surface in delivery_seen:
                errors.append(f"{rel} 交付面重复：{surface}")
            else:
                delivery_seen.add(surface)
                sl.delivery_surfaces.append(surface)
            continue
        if in_verify:
            if verify_base_indent is None and is_list:
                verify_base_indent = indent
            # Prose paragraphs and indented sub-bullets are documentation — tolerated,
            # not policed. Only top-level list items (at the base indent) are checks.
            if not is_list or (verify_base_indent is not None and indent > verify_base_indent):
                continue
            item = stripped[2:].strip()
            kind, target, surfaces, obligation_id = classify_check(item)
            if kind in ("assert", "judge", "human"):
                assert target is not None
                sl.checks.append(Check(kind, target, item, surfaces, obligation_id))
            elif kind == "broken":
                errors.append(f"{rel} 验证项 {target}：{item}")
            # "doc" → skip silently
    if not has_delivery:
        errors.append(f"{rel} 缺少 `## 交付面` 段；声明本 slice 实际交付的面（参考：{_suggested_surfaces()}）")
    elif not sl.delivery_surfaces:
        errors.append(f"{rel} `## 交付面` 至少声明一个交付面（参考：{_suggested_surfaces()}）")
    if not has_accept:
        errors.append(f"{rel} 缺少 `## 验收` 段")
    if not sl.checks:
        errors.append(f"{rel} 缺少验证项：`## 验证面` 至少声明一条 `[kind][面] <obligation-id>: <行为>`（或 legacy `[assert][面] \\`命令\\``）")
    if sl.delivery_surfaces:
        for check in sl.checks:
            for surface in check.surfaces:
                if surface not in sl.delivery_surfaces:
                    errors.append(f"{rel} 验证项声明 [{surface}]，但 `## 交付面` 未声明它：{check.raw}")
        for surface in sl.delivery_surfaces:
            tagged = [check for check in sl.checks if surface in check.surfaces]
            covered = [check for check in tagged if _surface_coverage_error(check, surface) is None]
            if not covered:
                reason = _surface_coverage_error(tagged[0], surface) if tagged else _coverage_requirement(surface)
                errors.append(f"{rel} 交付面 {surface} 未被有效验证覆盖；{reason}")
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


def _record_matches_check(record: dict, rk: str, check: Check) -> bool:
    """obligation_id 优先匹配；legacy fallback 到 command/item 字符串相等。"""
    if check.obligation_id:
        return rk == check.kind and record.get("obligation_id") == check.obligation_id
    if check.kind == "assert":
        return rk == "assert" and record.get("command") == check.target
    return rk == check.kind and record.get("item") == check.target


def check_state(check: Check, records: list[dict]) -> str:
    """passed | failed | recorded | missing — based on the latest matching record."""
    state = "missing"
    for record in records:
        rk = _record_kind(record)
        if not _record_matches_check(record, rk, check):
            continue
        if check.kind == "assert":
            state = "passed" if record.get("exit_code") == 0 else "failed"
        elif check.kind == "judge":
            verdict = record.get("verdict")
            if verdict == "pass":
                state = "passed"
            elif verdict == "fail":
                state = "failed"
        else:  # human
            if record.get("note"):
                state = "recorded"
    return state


def latest_judge_artifact(check: Check, records: list[dict]) -> str | None:
    """The artifact path on the latest passing judge record for this check, if any."""
    artifact = None
    for record in records:
        rk = _record_kind(record)
        if rk == "judge" and _record_matches_check(record, rk, check) and record.get("verdict") == "pass":
            artifact = record.get("artifact")
    return artifact


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
        entry = {
            "kind": check.kind,
            "obligation_id": check.obligation_id,
            "target": check.target,
            "surfaces": check.surfaces,
            "state": check_state(check, records),
        }
        # 仅 legacy assert（命令在 target）status 期能判 smoke；新格式 obligation 无命令不判
        if check.kind == "assert" and check.obligation_id is None:
            smoke, _ = looks_like_smoke(check.target)
            if smoke:
                entry["smoke"] = True
        if check.kind == "judge":
            artifact = latest_judge_artifact(check, records)
            if artifact:
                entry["artifact"] = artifact
        checks.append(entry)
    return {
        "id": sl.id,
        "title": sl.title,
        "done": sl.done,
        "file": f"slices/{sl.id}.md",
        "delivery_surfaces": sl.delivery_surfaces,
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
            surfaces = f"[{','.join(check['surfaces'])}]" if check.get("surfaces") else ""
            oid = check.get("obligation_id")
            label = f"{oid}：{check['target']}" if oid else check["target"]
            print(f"      {check['state']:<8} [{check['kind']}]{surfaces} {label}")
            if check.get("smoke"):
                print("        ⚠ 疑似烟雾测试（只证可达/可执行，不证语义）；建议改成会失败的断言或换 [judge]/[human]")
    if errors:
        print("结构问题：")
        for err in errors:
            print(f"  - {err}")
        return 1
    if next_slice:
        print(f"next: {next_slice}")
    else:
        print("全部 slice 通过正确性 gate（只保证正确且不回归，不代表体验质量达标；建议 review）")
    return 0


def _resolve_declared(sl: Slice, kind: str, slice_id: str, obligation: str | None, legacy_item: str | None) -> Check:
    """按 obligation_id 优先解析声明的 check；legacy fallback 到 target 字符串匹配。找不到 raise。"""
    if obligation:
        for c in sl.checks:
            if c.kind == kind and c.obligation_id == obligation:
                return c
        opts = [c.obligation_id for c in sl.checks if c.kind == kind and c.obligation_id] or ["（无）"]
        raise SeedError(
            f"{slice_id} 未声明 obligation `{obligation}` 的 [{kind}] 验证项；声明的：\n"
            + "\n".join(f"  - {opt}" for opt in opts)
        )
    item = normalize_text(legacy_item or "")
    for c in sl.checks:
        if c.kind == kind and c.obligation_id is None and c.target == item:
            return c
    if kind == "assert":
        opts = [c.target for c in sl.checks if c.kind == "assert" and c.obligation_id is None] or ["（无）"]
        raise SeedError(
            f"{slice_id} 未声明这条命令（legacy：命令须与 slices/{slice_id}.md 一致）；或改用 `--obligation <id>`。声明的：\n"
            + "\n".join(f"  - {opt}" for opt in opts)
        )
    opts = [c.target for c in sl.checks if c.kind == kind and c.obligation_id is None] or ["（无）"]
    raise SeedError(
        f"{slice_id} 未声明这条 [{kind}] 验证项；slices/{slice_id}.md 中声明的 {kind} 项：\n"
        + "\n".join(f"  - {opt}" for opt in opts)
    )


def cmd_run_check(
    root: Path,
    task: str,
    slice_id: str,
    cmd_tokens: list[str],
    *,
    mode: str,
    obligation: str | None,
    manual_item: str | None,
    judge_item: str | None,
    verdict: str | None,
    grade: str | None,
    trace: str | None,
    note: str | None,
    evidence: str | None,
    artifact: str | None,
    by: str | None,
    timeout: int,
) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)

    if mode == "judge":
        declared = _resolve_declared(sl, "judge", slice_id, obligation, judge_item)
        if verdict not in ("pass", "fail"):
            raise SeedError("judge 记录必须带 --verdict pass|fail")
        if not trace:
            raise SeedError("judge 记录必须带 --trace（裁判依据/证据指针，例如 rubric 文件 + 截图/输出位置）")
        record = {
            "slice": slice_id,
            "kind": "judge",
            "obligation_id": declared.obligation_id,
            "item": declared.target,
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
        if artifact:
            art_path = Path(artifact)
            if not art_path.is_absolute():
                art_path = root / artifact
            if not art_path.exists():
                raise SeedError(
                    f"--artifact 指向的文件不存在：{artifact}"
                    "（judge 须附它实际看过的截图/输出文件——视觉裁决看真实产物，不看代码）"
                )
            record["artifact"] = artifact
        path = _write_evidence(root, task, slice_id, record, None)
        print(f"{record['status']} (verdict={verdict}) → {path.relative_to(root)}")
        return 0 if verdict == "pass" else 1

    if mode == "human":
        declared = _resolve_declared(sl, "human", slice_id, obligation, manual_item)
        if not note:
            raise SeedError("human 记录必须带 --note（验证了什么、结论）")
        record = {
            "slice": slice_id,
            "kind": "human",
            "obligation_id": declared.obligation_id,
            "item": declared.target,
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
        raise SeedError("缺少要执行的命令：seed run-check <task> --slice S-NNN --obligation <id> -- <command>")
    command = normalize_command(" ".join(cmd_tokens))
    declared = _resolve_declared(sl, "assert", slice_id, obligation, command)
    # 烟雾硬挡：非 compliance 交付面的 obligation/命令，烟雾命令拒绝落盘（防线不降反升）；
    # compliance 面允许烟雾 + 软警告。
    smoke, reason = looks_like_smoke(command)
    if smoke:
        blocked = [s for s in declared.surfaces if s != "compliance"]
        if blocked:
            raise SeedError(
                f"烟雾命令不能兑现交付面 {blocked} 的验证：{reason}。"
                "改成会失败的断言（测试套件/契约回放/Playwright spec），或把验证项标 [compliance]。"
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
        "obligation_id": declared.obligation_id,
        "command": command,
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "created_at": _now(),
    }
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
            label = f"{check.obligation_id}：{check.target}" if check.obligation_id else check.target
            gaps.append(f"[{check.kind}] {label} → {state}")
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
    if remaining:
        print(f"next: {remaining[0]}")
    else:
        print("全部 slice 通过正确性 gate。注意：gate 只保证正确且不回归，不代表体验质量达标——触发 review 做语义与质量对账。")
    return 0


# --- entry ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seed",
        description="seed-kit helper：prd.md checkbox + evidence 是唯一状态；done 只认 run-check 落盘的证据。",
    )
    parser.add_argument("--root", default=".", help="项目根目录（含 .arbor/）")
    sub = parser.add_subparsers(dest="command", required=True)

    new_parser = sub.add_parser("new", help="脚手架 .arbor/tasks/<task>/：prd.md 模板 + slices/S-001.md")
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
    rc_parser.add_argument("--obligation", help="验证义务 id：绑到 slices/S-NNN.md 声明的 <obligation-id>；三 kind 共用，优先于 --judge/--human/命令字面匹配")
    rc_parser.add_argument("--judge", help="[judge] 验证项原文（legacy：obligation 格式改用 --obligation；由独立 agent 在 fresh session 裁决后记录）")
    rc_parser.add_argument("--verdict", choices=["pass", "fail"], help="judge：裁决结果")
    rc_parser.add_argument("--grade", help="judge：评分/等级（可选）")
    rc_parser.add_argument("--trace", help="judge：裁决依据/证据指针（rubric + 截图/输出位置）")
    rc_parser.add_argument("--human", help="[human] 验证项原文")
    rc_parser.add_argument("--manual", help="[manual] 验证项原文（旧式，等同 --human）")
    rc_parser.add_argument("--note", help="human/judge：验证了什么、结论")
    rc_parser.add_argument("--evidence", help="human：证据指针（截图路径/输出位置，可选）")
    rc_parser.add_argument("--artifact", help="judge：裁决时实际看过的截图/输出文件路径（提供则 helper 校验它真实存在）")
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
            elif args.verdict is not None:
                mode, manual_item, judge_item = "judge", None, None  # obligation judge（--obligation <id> --verdict）
            elif args.obligation is not None and args.note:
                mode, manual_item, judge_item = "human", None, None  # obligation human（--obligation <id> --note）
            else:
                mode, manual_item, judge_item = "assert", None, None
            return cmd_run_check(
                root,
                args.task,
                args.slice_id,
                cmd_tokens,
                mode=mode,
                obligation=args.obligation,
                manual_item=manual_item,
                judge_item=judge_item,
                verdict=args.verdict,
                grade=args.grade,
                trace=args.trace,
                note=args.note,
                evidence=args.evidence,
                artifact=args.artifact,
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
