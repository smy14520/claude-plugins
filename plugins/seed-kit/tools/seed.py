#!/usr/bin/env python3
"""seed — seed-kit 的最小 PRD checkbox 状态 helper。

状态模型：`.arbor/tasks/<task>/prd.md` 的 slice checkbox + `evidence/` 是唯一持久状态。
无 task.json，无状态机。单一归属：prd.md 的 `## Slices` 段是有序 checkbox 索引
（每个 slice 一行）；每个 slice 的验收 + 验证项只写在 `slices/S-NNN.md`。

验证有三种 kind——封闭词汇，回答"什么让 passed 可信，谁/什么在断言"：

- `assert`  —— 真正会失败的命令（失败时必须 exit 非零：测试套件、契约回放、
  Playwright spec）。gate：exit_code == 0 → passed。裸探针（不带 `--fail` 的
  `curl`、`echo`）只证明"它运行了"，不证明"它正确"；对非 compliance 交付面，
  seed 在 run-check 时*拒绝*这类命令；对 compliance 交付面则接受但警告——
  真正的验证需要会失败的断言命令。
- `judge`  —— 由独立 agent（生成者 ≠ 验证者，详见 verification）按 AC rubric 裁决。
  gate：记录的 verdict == pass；verdict 可由 legacy `--verdict` 给出，也可由
  `--rubric + --score-file` 机械计算。helper 只记录/校验证据形状与计算结果；裁决本身
  是 skill 层动作（helper 永不调用 LLM）。
- `human`  —— 真人 stakeholder 签收（品味、合规、按定义无法自动化的事项）。
  gate：带 note + 签收人的记录。

旧式形式仍可用：行首反引号包裹的 `` `命令` `` 项视为 `assert`；`[manual]` 项视为 `human`。

唯一的硬 gate：`seed done` 仅当 slice 文件声明的每条验证项都按 kind 记录了正确形状
的证据时，才勾选 checkbox（assert：passed；judge：pass verdict；human：签收记录）。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
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
COMMAND_IN_REST_RE = re.compile(r"^`([^`]+)`")  # legacy：[assert] 命令在行首反引号内，尾部注释忽略
OBLIGATION_RE = re.compile(r"^\s*([^:`][^:]*?)\s*:\s*(.+)$", re.DOTALL)  # 新格式：<obligation-id>: <可观测行为>。注意 [^:`] 排除冒号（避免空 id 行 `: 行为`）和反引号（避免匹配 legacy 的 `` 命令` ``）
MANUAL_ITEM_RE = re.compile(r"^\[manual\]\s*(.+)$")
KIND_PREFIX_RE = re.compile(
    r"^\[(assert|judge|human)\](?:\s*\[([a-z0-9._-]+(?:\s*,\s*[a-z0-9._-]+)*)\])?\s*(.*)$",
    re.DOTALL,
)
SLICES_SECTION = "## Slices"
# 参考词汇表（非封闭）：常见 Web 产品的交付面示例。项目可用任意面名（游戏 gameplay、CLI cli-dx、
# 数据管道 data-quality 等）——helper 只校验"声明的交付面被验证项覆盖"（集合关系，面名字无关），
# 不限定面名，也不规定"该面应使用 assert/judge/human 的哪种 kind"（交项目 .claude/rules + review）。
SUGGESTED_SURFACES = ("backend-domain", "api", "web-ui", "e2e", "compliance", "infra")

# 磁盘上 evidence 的 kind 别名，兼容三 kind 词汇表出现前的旧记录。
KIND_ALIASES = {"automated": "assert", "manual": "human"}

# 无论功能实际做什么都 exit 0 的命令——标记为烟雾测试。
SMOKE_TOOL_RE = re.compile(r"(?:^|[\s|&;])(curl|wget)(?:[\s|&;]|$)")


class SeedError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_command(command: str) -> str:
    # 仅合并空白。不要通过 shlex 往返——它会重新引号 shell 元字符（括号、&&、|），破坏其执行。
    return " ".join(command.split())


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def _has_fail_flag(command: str) -> bool:
    """检查 curl/wget 是否带 --fail（或 -f，包括组合形式如 -sf）。"""
    for tok in command.split():
        if tok == "--fail" or tok.startswith("--fail="):
            return True
        if tok.startswith("-") and not tok.startswith("--") and "f" in tok:
            return True
    return False


def looks_like_smoke(command: str) -> tuple[bool, str]:
    """高精度烟雾启发式：仅当命令无论功能实际做什么都 exit 0 时返回 True。
    保守策略——假阴性可接受，假阳性不可接受。"""
    if not command.strip():
        return False, ""
    first = command.strip().split()[0]
    # 裸 curl/wget 不带 --fail 且未管道/链式接到断言工具
    if SMOKE_TOOL_RE.search(command):
        if _has_fail_flag(command):
            return False, ""
        if any(op in command for op in ("|", "&&", "||")):
            return False, ""
        return True, "curl/wget 无 --fail 且无管道/链式断言：只证路由可达，不证语义正确"
    # echo / true / : 后面没有断言链
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
    # 新格式的 obligation assert 命令在 run-check 时才绑定，parse 期跳过，run-check 期拒绝并报错。
    # 不按面名规定 kind——"该面使用 assert/judge/human 的取舍"是项目标准（写 .claude/rules），交 review 查"验证降级"。
    if check.kind == "assert" and check.obligation_id is None and looks_like_smoke(check.target)[0]:
        return "smoke assert 只证可达/可执行，不覆盖交付面"
    return None


def _coverage_requirement(surface: str) -> str:
    return f"{surface} 需要至少一条非烟雾的验证项覆盖（该面使用 assert/judge/human 的取舍由项目标准定，见 .claude/rules）"


def classify_check(item: str) -> tuple[str, str | None, list[str], str | None]:
    r"""分类一条验证项列表项。

    返回以下之一：
      (kind, target, surfaces, obligation_id) — 识别出的 check（kind ∈ assert/judge/human）
      ("doc", None, [], None)      — 文档行，静默跳过
      ("broken", msg, [], None)    — 格式错误的 kind 标签项或 surface 标签

    带前缀的项（`[kind][surface] <rest>`）有两种形式：
      obligation: `<obligation-id>: <可观测行为>`（冒号分隔；id 不以冒号开头，避免与空 id 行 `: 行为` 冲突）
                  → obligation_id = id, target = 行为描述。命令不在 slice，run-check 时按
                    `--obligation <id>` 绑定。
      legacy:     assert 行首反引号 `命令`，或 judge/human 纯文本描述
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
            return ("broken", "声明了 [assert] 但没有 `<obligation-id>: <行为>` 或反引号命令", [], None)
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
    """解析 prd.md 的 `## Slices` checkbox 索引以及每个 slices/S-NNN.md。

    prd.md 拥有顺序 + 状态（每个 slice 一行 `### [ ] S-NNN 标题`）；
    slices/S-NNN.md 拥有验收 + 验证项。没有任何内容写两遍。
    返回 (slices, structural errors)。
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
    """去除 HTML 注释块；返回（原始索引, 行）用于其余内容。"""
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
    """解析 slices/S-NNN.md 为交付面 + checks。返回结构错误。"""
    rel = f"slices/{sl.id}.md"
    file_path = slices_dir / f"{sl.id}.md"
    if not file_path.is_file():
        return [f"缺少 {rel}：slice 的验收与验证项都写在该文件中"]
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
            # 非列表项（散文段落）与缩进子项视为文档，容忍但不主动管理；
            # 仅顶层列表项（在基础缩进层级）才是验证项。
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
        errors.append(f"{rel} 缺少验证项：`## 验证面` 至少声明一条 `[kind][面] <obligation-id>: <行为>`（或 legacy 行首反引号包裹命令的形式）")
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
    return "passed"  # assert 与 judge 都靠 passing 结果过关


def _record_matches_check(record: dict, rk: str, check: Check) -> bool:
    """obligation_id 优先匹配；legacy fallback 到 command/item 字符串相等。"""
    if check.obligation_id:
        return rk == check.kind and record.get("obligation_id") == check.obligation_id
    if check.kind == "assert":
        return rk == "assert" and record.get("command") == check.target
    return rk == check.kind and record.get("item") == check.target


def _judge_state_from_verdict(verdict: object) -> str | None:
    if verdict == "pass":
        return "passed"
    if verdict == "fail":
        return "failed"
    return None


def check_state(check: Check, records: list[dict]) -> str:
    """passed | failed | recorded | missing —— 基于最新的匹配记录。"""
    state = "missing"
    for record in records:
        rk = _record_kind(record)
        if not _record_matches_check(record, rk, check):
            continue
        if check.kind == "assert":
            state = "passed" if record.get("exit_code") == 0 else "failed"
        elif check.kind == "judge":
            judge_state = _judge_state_from_verdict(record.get("verdict"))
            if judge_state:
                state = judge_state
        else:  # human
            if record.get("note"):
                state = "recorded"
    return state


def latest_matching_record(check: Check, records: list[dict]) -> dict | None:
    """该 check 最新一条匹配 evidence（如有）。"""
    latest = None
    for record in records:
        rk = _record_kind(record)
        if _record_matches_check(record, rk, check):
            latest = record
    return latest


def latest_judge_artifact(check: Check, records: list[dict]) -> str | None:
    """该 check 最新一条 passing judge 记录的 artifact 路径（如有）。"""
    artifact = None
    for record in records:
        rk = _record_kind(record)
        if rk == "judge" and _record_matches_check(record, rk, check) and record.get("verdict") == "pass":
            artifact = record.get("artifact")
    return artifact


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


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _score_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SeedError(f"{field} 必须是数字")
    return float(value)


def _compute_score_verdict(rubric: dict, score_doc: dict) -> tuple[str, dict]:
    dimensions = rubric.get("dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        raise SeedError("rubric 必须包含非空 object 字段 dimensions")
    scores = score_doc.get("scores")
    if not isinstance(scores, dict):
        raise SeedError("score-file 必须包含 object 字段 scores")

    rubric_id = rubric.get("id")
    score_rubric_id = score_doc.get("rubric_id")
    if rubric_id is not None and not isinstance(rubric_id, str):
        raise SeedError("rubric.id 必须是字符串")
    if score_rubric_id is not None and not isinstance(score_rubric_id, str):
        raise SeedError("score-file.rubric_id 必须是字符串")
    if rubric_id and score_rubric_id and rubric_id != score_rubric_id:
        raise SeedError(f"score-file.rubric_id={score_rubric_id} 与 rubric.id={rubric_id} 不一致")

    scale = rubric.get("scale", {})
    if scale is None:
        scale = {}
    if not isinstance(scale, dict):
        raise SeedError("rubric.scale 必须是 object")
    scale_min = _score_number(scale["min"], "rubric.scale.min") if "min" in scale else None
    scale_max = _score_number(scale["max"], "rubric.scale.max") if "max" in scale else None
    if scale_min is not None and scale_max is not None and scale_min > scale_max:
        raise SeedError("rubric.scale.min 不能大于 rubric.scale.max")

    unknown = sorted(set(scores) - set(dimensions))
    if unknown:
        raise SeedError("score-file 包含 rubric 未声明的维度：" + ", ".join(unknown))

    weighted_sum = 0.0
    weight_total = 0.0
    details: dict[str, dict] = {}
    failed_dimensions: list[str] = []
    for name, spec in dimensions.items():
        if not isinstance(name, str) or not name:
            raise SeedError("rubric.dimensions 的 key 必须是非空字符串")
        if not isinstance(spec, dict):
            raise SeedError(f"rubric.dimensions.{name} 必须是 object")
        if "min" not in spec:
            raise SeedError(f"rubric.dimensions.{name}.min 缺失")
        minimum = _score_number(spec["min"], f"rubric.dimensions.{name}.min")
        # weight 默认 1（向后兼容）
        weight = _score_number(spec["weight"], f"rubric.dimensions.{name}.weight") if "weight" in spec else 1.0
        if name not in scores:
            raise SeedError(f"score-file 缺少维度分数：{name}")
        raw = scores[name]
        # 兼容两种格式：纯数值 vs {score, rationale}
        if isinstance(raw, dict):
            value = _score_number(raw.get("score"), f"score-file.scores.{name}.score")
            rationale = str(raw.get("rationale", "")).strip()
            # 新格式 rationale 必填，旧格式（纯数值）允许空
            if not rationale:
                raise SeedError(f"score-file.scores.{name}.rationale 缺失（评分必须给依据）")
        else:
            value = _score_number(raw, f"score-file.scores.{name}")
            rationale = ""  # 旧格式允许无 rationale
        if scale_min is not None and value < scale_min:
            raise SeedError(f"score-file.scores.{name} 小于 rubric.scale.min")
        if scale_max is not None and value > scale_max:
            raise SeedError(f"score-file.scores.{name} 大于 rubric.scale.max")
        passed = value >= minimum
        if not passed:
            failed_dimensions.append(name)
        weighted_sum += value * weight
        weight_total += weight
        details[name] = {"score": value, "min": minimum, "passed": passed, "weight": weight}
        if rationale:
            details[name]["rationale"] = rationale

    average = weighted_sum / weight_total if weight_total else 0.0
    aggregate = rubric.get("aggregate", {})
    if aggregate is None:
        aggregate = {}
    if not isinstance(aggregate, dict):
        raise SeedError("rubric.aggregate 必须是 object")
    min_average = None
    average_passed = True
    if "min_average" in aggregate:
        min_average = _score_number(aggregate["min_average"], "rubric.aggregate.min_average")
        average_passed = average >= min_average
    failed = list(failed_dimensions)
    if not average_passed:
        failed.append("__average__")
    verdict = "pass" if not failed else "fail"
    summary = {
        "average": average,
        "failed_dimensions": failed,
        "dimensions": details,
    }
    if min_average is not None:
        summary["min_average"] = min_average
        summary["average_passed"] = average_passed
    return verdict, summary


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
            latest = latest_matching_record(check, records)
            if latest:
                for key in ("verdict", "artifact", "rubric", "score_file", "score_summary"):
                    if key in latest:
                        entry[key] = latest[key]
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
        print("全部 slice 的声明义务已过 gate（未声明维度仍需 review；质量没有上限）")
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
    rubric: str | None,
    score_file: str | None,
    aggregation_file: str | None,
    by: str | None,
    timeout: int,
) -> int:
    slices = _require_valid_prd(root, task)
    sl = _find_slice(slices, slice_id)

    if mode == "judge":
        declared = _resolve_declared(sl, "judge", slice_id, obligation, judge_item)
        scored = score_file is not None or rubric is not None or aggregation_file is not None
        if scored:
            if verdict is not None:
                raise SeedError("scoring judge 的 verdict 由 --rubric + --score-file/--aggregation-file 计算，不能同时手写 --verdict")
            if not rubric:
                raise SeedError("scoring judge 必须提供 --rubric")
            if score_file and aggregation_file:
                raise SeedError("--score-file 和 --aggregation-file 互斥，只能提供一个")
            if not score_file and not aggregation_file:
                raise SeedError("scoring judge 必须提供 --score-file 或 --aggregation-file")
            if not artifact:
                raise SeedError("scoring judge 必须附 --artifact（评分必须基于真实产物）")
            rubric_path, rubric_data = _load_json_object(root, rubric, "--rubric")
            if aggregation_file:
                # 读取 aggregation-file，转换为 score_doc 格式
                agg_path, agg_data = _load_json_object(root, aggregation_file, "--aggregation-file")
                score_data = {
                    "rubric_id": agg_data.get("rubric_id"),
                    "scores": {name: dim["score"] for name, dim in agg_data.get("dimensions", {}).items()}
                }
                score_path = agg_path
            else:
                score_path, score_data = _load_json_object(root, score_file, "--score-file")
            verdict, score_summary = _compute_score_verdict(rubric_data, score_data)
        else:
            if verdict not in ("pass", "fail"):
                raise SeedError("judge 记录必须带 --verdict pass|fail，或使用 --rubric + --score-file")
            score_summary = None
            rubric_path = None
            rubric_data = None
            score_path = None
            score_data = None
        if not trace:
            raise SeedError("judge 记录必须带 --trace（裁判依据/证据指针，例如 rubric 文件 + 截图/输出位置）")
        if verdict == "pass" and not artifact:
            raise SeedError("judge verdict=pass 必须附 --artifact（截图/输出等真实产物）；无产物不能记 pass")
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
        if scored:
            record["verdict_source"] = "aggregation-file" if aggregation_file else "score-file"
            record["rubric"] = rubric
            record["rubric_sha256"] = _file_sha256(rubric_path)
            if rubric_data and rubric_data.get("id"):
                record["rubric_id"] = rubric_data["id"]
            if aggregation_file:
                record["aggregation_file"] = aggregation_file
                record["aggregation_file_sha256"] = _file_sha256(score_path)
            else:
                record["score_file"] = score_file
            record["score_summary"] = score_summary
            if isinstance(score_data, dict) and "summary" in score_data:
                record["score_summary_text"] = score_data["summary"]
        if grade:
            record["grade"] = grade
        if note:
            record["note"] = note
        if artifact:
            art_path = _project_path(root, artifact)
            if not art_path.exists():
                raise SeedError(
                    f"--artifact 指向的文件不存在：{artifact}"
                    "（judge 须附实际看过的截图/输出——裁决基于产物，不基于代码）"
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
    # 烟雾命令硬阻断：非 compliance 交付面的 obligation/命令，烟雾命令拒绝落盘；
    # compliance 面允许烟雾命令，但发出一条软警告（不阻断）。
    smoke, reason = looks_like_smoke(command)
    if smoke:
        blocked = [s for s in declared.surfaces if s != "compliance"]
        if blocked:
            raise SeedError(
                f"烟雾命令无法覆盖交付面 {blocked} 的验证需求：{reason}。"
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
        print("全部 slice 的声明义务已过 gate。注意：未声明维度仍需 review；质量没有上限。")
    return 0


def cmd_review_mark(
    root: Path,
    task: str,
    slice_id: str,
    *,
    verdict: str,
    round_num: int | None,
    note: str | None,
) -> int:
    """落 review-loop 终态 marker（done 的 PreToolUse gate 查它）。

    review-loop Workflow 不能写文件，故由 command 跑完 loop 后调本命令，把
    terminal_reason 落 evidence/<slice>/review-loop.json。done gate（review_gate.py）
    要求 terminal_reason == converged 才放行勾选。
    """
    slices = _require_valid_prd(root, task)
    _find_slice(slices, slice_id)  # 校验 slice 存在，防 marker 写到错地方
    directory = evidence_dir(root, task, slice_id)
    directory.mkdir(parents=True, exist_ok=True)
    record = {
        "task": task,
        "slice": slice_id,
        "terminal_reason": verdict,
        "converged": verdict == "converged",
        "round": round_num,
        "note": note,
        "written_at": _now(),
    }
    marker = directory / "review-loop.json"
    marker.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outcome = "可推进 done" if verdict == "converged" else "不推 done（review-loop 未收敛，交人）"
    print(f"review-loop marker 已落盘：{verdict} — {outcome}")
    print(f"  {marker}")
    return 0


def cmd_score_aggregate(root: Path, rubric_path: str, score_files: list[str], out_path: str) -> int:
    """聚合多个 score-file，输出 median 结果。"""
    try:
        # 1. 加载 rubric
        _, rubric = _load_json_object(root, rubric_path, "--rubric")
        dimensions = rubric.get("dimensions", {})

        if not isinstance(dimensions, dict) or not dimensions:
            raise SeedError("rubric 必须包含非空 object 字段 dimensions")

        # 2. 加载所有 score-file
        all_scores = []
        for sf_path in score_files:
            _, score_doc = _load_json_object(root, sf_path, f"--score-files ({sf_path})")
            all_scores.append(score_doc)

        if not all_scores:
            raise SeedError("至少需要一个 score-file")

        # 3. 按维度聚合（median）
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
                # 兼容两种格式：number 或 {score, rationale}
                if isinstance(raw, dict):
                    value = _score_number(raw.get("score", 0), f"score-file ({score_files[i]}).scores.{dim_name}.score")
                else:
                    value = _score_number(raw, f"score-file ({score_files[i]}).scores.{dim_name}")
                score_values.append(value)
                judge_scores[f"judge-{i+1}"] = value

            if not score_values:
                raise SeedError(f"维度 {dim_name} 在所有 score-file 中都不存在")

            # 计算 median
            score_values_sorted = sorted(score_values)
            n = len(score_values_sorted)
            if n % 2 == 0:
                median = (score_values_sorted[n//2 - 1] + score_values_sorted[n//2]) / 2
            else:
                median = score_values_sorted[n//2]

            aggregated[dim_name] = {
                "score": median,
                "judge_scores": judge_scores,
                "range": max(score_values) - min(score_values),
                "min": min(score_values),
                "max": max(score_values)
            }

        # 4. 计算平均
        total = sum(d["score"] for d in aggregated.values())
        average = total / len(aggregated) if aggregated else 0.0

        # 5. 构建输出
        output = {
            "rubric_id": rubric.get("id"),
            "method": "median",
            "judges": [f"judge-{i+1}" for i in range(len(all_scores))],
            "dimensions": aggregated,
            "average": average,
            "source_files": score_files
        }

        # 6. 写入文件
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
    rc_parser.add_argument("--obligation", help="验证义务 id：绑到 slices/S-NNN.md 声明的 <obligation-id>；三 kind 共用，优先于 --judge/--human 与命令字面匹配")
    rc_parser.add_argument("--judge", help="[judge] 验证项原文。obligation 格式请改用 --obligation；由独立 agent 裁决后记录（详见 verification）")
    rc_parser.add_argument("--verdict", choices=["pass", "fail"], help="judge：legacy 二值裁决结果；scoring judge 改用 --rubric + --score-file 计算")
    rc_parser.add_argument("--grade", help="judge：评分/等级自由文本（可选备注，不参与 gate）")
    rc_parser.add_argument("--rubric", help="judge scoring gate：项目提供的机器可读 rubric JSON")
    rc_parser.add_argument("--score-file", help="judge scoring gate：独立 judge 产出的结构化 score JSON")
    rc_parser.add_argument("--aggregation-file", help="judge scoring gate（多裁判模式）：聚合后的 score JSON（与 --score-file 互斥）")
    rc_parser.add_argument("--trace", help="judge：裁决依据/证据指针（rubric + 截图/输出位置）")
    rc_parser.add_argument("--human", help="[human] 验证项原文")
    rc_parser.add_argument("--manual", help="[manual] 验证项原文（旧式，等同 --human）")
    rc_parser.add_argument("--note", help="human/judge：验证了什么、结论")
    rc_parser.add_argument("--evidence", help="human：证据指针（截图路径/输出位置，可选）")
    rc_parser.add_argument("--artifact", help="judge：裁决时实际看过的截图/输出文件路径（提供时 helper 会校验其存在性）")
    rc_parser.add_argument("--by", help="human/judge：签收人/裁决者（默认 user / independent-judge）")
    rc_parser.add_argument("--timeout", type=int, default=600)

    done_parser = sub.add_parser("done", help="证据齐备后勾选 slice checkbox（唯一合法勾选入口）")
    done_parser.add_argument("task")
    done_parser.add_argument("--slice", dest="slice_id", required=True)

    rm_parser = sub.add_parser("review-mark", help="落 review-loop 终态 marker（done gate 查它：converged 才放行）")
    rm_parser.add_argument("task")
    rm_parser.add_argument("--slice", dest="slice_id", required=True)
    rm_parser.add_argument(
        "--verdict",
        required=True,
        choices=["converged", "assert-stalled", "assert-unavailable", "reviewer-blind", "circuit-breaker", "rounds-exhausted"],
        help="review-loop 的 terminal_reason（Workflow 返回值）；只有 converged 能推进 done",
    )
    rm_parser.add_argument("--round", dest="round_num", type=int)
    rm_parser.add_argument("--note", help="备注（如 escalated 原因）")

    # score 子命令组
    score_parser = sub.add_parser("score", help="评分聚合")
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
            elif args.verdict is not None or args.score_file is not None or args.rubric is not None or args.aggregation_file is not None:
                mode, manual_item, judge_item = "judge", None, None  # obligation judge（--obligation <id> --verdict 或 --rubric + --score-file/--aggregation-file）
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
                rubric=args.rubric,
                score_file=args.score_file,
                aggregation_file=args.aggregation_file,
                by=args.by,
                timeout=args.timeout,
            )
        if args.command == "done":
            return cmd_done(root, args.task, args.slice_id)
        if args.command == "review-mark":
            return cmd_review_mark(
                root,
                args.task,
                args.slice_id,
                verdict=args.verdict,
                round_num=args.round_num,
                note=args.note,
            )
        if args.command == "score":
            if args.score_cmd == "aggregate":
                return cmd_score_aggregate(root, args.rubric, args.score_files, args.out)
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
