#!/usr/bin/env python3
"""forge — tinder-kit 的轻量任务脚手架与看板工具。

设计原则：
1. 单一定义点：绝不做双重记账。
   - 任务元数据（title, phase）：在 state.json
   - 深接缝（Seams）与契约：在 spec.md
   - 交接链：在 handoffs/*.md
   - 交付背书：在 endorsement.md
2. 状态即文件：Agent 使用原生 Edit/Write 工具直接修改文件，享受终端 Diff 与 Undo。
   forge CLI 仅提供人类/初始化高频动作（new, status, root），不充当 CRUD 中间商。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ForgeError(Exception):
    """Forge 工具基础异常。"""
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plugin_root() -> Path:
    """定位 tinder-kit 插件根目录。"""
    return Path(__file__).resolve().parents[1]


def forge_root(repo_root: Path) -> Path:
    """定位项目的 .forge 目录。"""
    return repo_root / ".forge"


def tasks_root(repo_root: Path) -> Path:
    """定位项目的 .forge/tasks 目录。"""
    return forge_root(repo_root) / "tasks"


def task_dir(repo_root: Path, slug: str) -> Path:
    return tasks_root(repo_root) / slug


def state_path(repo_root: Path, slug: str) -> Path:
    return task_dir(repo_root, slug) / "state.json"


def spec_path(repo_root: Path, slug: str) -> Path:
    return task_dir(repo_root, slug) / "spec.md"


def handoffs_dir(repo_root: Path, slug: str) -> Path:
    return task_dir(repo_root, slug) / "handoffs"


def endorsement_path(repo_root: Path, slug: str) -> Path:
    return task_dir(repo_root, slug) / "endorsement.md"


@dataclass
class TaskState:
    slug: str
    title: str
    phase: str = "ALIGN"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskState:
        return cls(
            slug=data["slug"],
            title=data.get("title", data["slug"]),
            phase=data.get("phase", "ALIGN"),
            created_at=data.get("created_at", _now()),
            updated_at=data.get("updated_at", _now()),
        )


def read_state(repo_root: Path, slug: str) -> TaskState:
    path = state_path(repo_root, slug)
    if not path.is_file():
        raise ForgeError(f"未找到任务状态文件：{path}（可使用 `forge new {slug}` 创建）")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return TaskState.from_dict(data)
    except json.JSONDecodeError as exc:
        raise ForgeError(f"状态文件 JSON 解析失败：{path} ({exc})")


def write_state(repo_root: Path, state: TaskState) -> None:
    path = state_path(repo_root, state.slug)
    state.updated_at = _now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_task_seams(repo_root: Path, slug: str) -> list[str]:
    """从 spec.md 动态解析深接缝，绝不双重记账。"""
    spec_file = spec_path(repo_root, slug)
    if not spec_file.is_file():
        return []
    lines = spec_file.read_text(encoding="utf-8").splitlines()
    seams: list[str] = []
    in_seams = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Agreed Seams"):
            in_seams = True
            continue
        elif in_seams and stripped.startswith("## "):
            in_seams = False
            continue
        if in_seams and (stripped.startswith("- **Seam") or (stripped.startswith("- `") and "->" in stripped)):
            if "[定义" not in stripped and "[TODO]" not in stripped:
                seams.append(stripped)
    return seams


def get_task_handoffs(repo_root: Path, slug: str) -> list[str]:
    """从 handoffs 目录动态扫描交接文件，天然保持时间序。"""
    hdir = handoffs_dir(repo_root, slug)
    if not hdir.is_dir():
        return []
    return sorted([f.name for f in hdir.glob("*.md")])


# --- CLI Commands -------------------------------------------------------------

def cmd_new(repo_root: Path, slug: str, title: str | None) -> int:
    if not SLUG_RE.match(slug):
        raise ForgeError(f"无效的任务名：'{slug}'。只允许小写字母、数字、点、减号与下划线。")

    tdir = task_dir(repo_root, slug)
    if tdir.exists():
        raise ForgeError(f"任务 '{slug}' 已经存在：{tdir}")

    tdir.mkdir(parents=True, exist_ok=True)
    handoffs_dir(repo_root, slug).mkdir(parents=True, exist_ok=True)

    task_title = title.strip() if title else slug
    state = TaskState(slug=slug, title=task_title)
    write_state(repo_root, state)

    # 从模板写入初始 spec.md
    tmpl_path = plugin_root() / "templates" / "spec.md"
    if tmpl_path.is_file():
        tmpl_content = tmpl_path.read_text(encoding="utf-8")
        spec_content = tmpl_content.format(
            title=task_title,
            goal="[描述核心问题与预期交付效果]",
            seam_1_signature="[定义深接口函数/模块]",
            seam_1_behavior="[定义端到端行为预期]",
            seam_1_test="[定义行为测试命令]",
            out_of_scope_item="[明确排除的功能]",
        )
    else:
        spec_content = f"# {task_title}\n\n## Goal\n\n## Agreed Seams\n\n## Out of Scope\n"

    spec_path(repo_root, slug).write_text(spec_content, encoding="utf-8")

    print(f"已创建新任务 '{slug}' ({task_title}) ✓")
    print(f"  工作区: {tdir.relative_to(repo_root)}")
    print(f"  名片档: {state_path(repo_root, slug).relative_to(repo_root)}")
    print(f"  规格档: {spec_path(repo_root, slug).relative_to(repo_root)}")
    return 0


def cmd_status(repo_root: Path, slug: str | None, json_output: bool) -> int:
    base = tasks_root(repo_root)
    task_dirs = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []

    if slug is None:
        if not task_dirs:
            print("目前没有任何任务；使用 `forge new <slug>` 创建。")
            return 0
        if json_output:
            out_list = []
            for p in task_dirs:
                try:
                    st = read_state(repo_root, p.name)
                    seams = get_task_seams(repo_root, p.name)
                    handoffs = get_task_handoffs(repo_root, p.name)
                    has_endorsement = endorsement_path(repo_root, p.name).is_file()
                    out_list.append({
                        **st.to_dict(),
                        "seams_count": len(seams),
                        "handoffs": handoffs,
                        "endorsed": has_endorsement,
                    })
                except Exception:
                    pass
            print(json.dumps(out_list, indent=2, ensure_ascii=False))
            return 0

        print(f"任务列表 ({len(task_dirs)} 个任务)：")
        for p in task_dirs:
            try:
                st = read_state(repo_root, p.name)
                seams = get_task_seams(repo_root, p.name)
                handoffs = get_task_handoffs(repo_root, p.name)
                latest_h = f"最新交接: {handoffs[-1]}" if handoffs else "无交接记录"
                print(f"  • [{st.phase}] {st.slug}: {st.title}")
                print(f"    └─ Seams: {len(seams)} | {latest_h}")
            except Exception:
                print(f"  • {p.name} (损坏或无法读取)")
        return 0

    state = read_state(repo_root, slug)
    seams = get_task_seams(repo_root, slug)
    handoffs = get_task_handoffs(repo_root, slug)
    endorsed = endorsement_path(repo_root, slug).is_file()

    if json_output:
        data = {
            **state.to_dict(),
            "seams": seams,
            "handoffs": handoffs,
            "endorsed": endorsed,
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    print(f"任务: {state.slug} ({state.title})")
    print(f"  当前阶段: {state.phase} | 更新时间: {state.updated_at}")
    print(f"  核心 Seams ({len(seams)} 个, 动态自 spec.md):")
    if seams:
        for idx, s in enumerate(seams, 1):
            print(f"    {idx}. {s}")
    else:
        print("    (尚未在 spec.md 中锁定 Seams 接缝)")

    print(f"  交接文档链 ({len(handoffs)} 份, 动态自 handoffs/):")
    if handoffs:
        for h in handoffs:
            print(f"    - {h}")
    else:
        print("    (暂无交接记录)")

    print(f"  交付背书: {'已完成 (endorsement.md 就绪) ✓' if endorsed else '未完成'}")
    return 0


# --- Entrypoint ---------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge", description="tinder-kit 极简任务与看板工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # root
    sub.add_parser("root", help="输出 tinder-kit 插件根目录")

    # new
    p_new = sub.add_parser("new", help="创建新任务")
    p_new.add_argument("slug", help="任务 slug（小写字母、数字、连字符）")
    p_new.add_argument("--title", help="任务中文/人类可读标题")

    # status
    p_status = sub.add_parser("status", help="查询任务状态或列出所有任务")
    p_status.add_argument("slug", nargs="?", help="任务 slug（缺省列出全部）")
    p_status.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    try:
        if args.cmd == "root":
            print(plugin_root())
            return 0
        elif args.cmd == "new":
            return cmd_new(repo_root, args.slug, args.title)
        elif args.cmd == "status":
            return cmd_status(repo_root, args.slug, args.json)
    except ForgeError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
