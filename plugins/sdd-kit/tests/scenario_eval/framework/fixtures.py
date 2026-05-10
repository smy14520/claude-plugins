"""Workspace preparation and file utilities for scenario eval runs."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import EnvConfig

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = PLUGIN_ROOT / "tests"
FIXTURE_DIR = TESTS_ROOT / "fixtures" / "express-app"
RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"


@dataclass
class ScenarioPaths:
    run_dir: Path
    work_dir: Path
    transcript_path: Path
    dialogue_path: Path
    summary_path: Path
    events_path: Path
    test_report_path: Path


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "scenario"


def unique_path(base: Path) -> Path:
    if not base.exists():
        return base
    suffix = 2
    while Path(f"{base}-{suffix}").exists():
        suffix += 1
    return Path(f"{base}-{suffix}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_dialogue(paths: ScenarioPaths, title: str, body: str) -> None:
    paths.dialogue_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.dialogue_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n\n{body.strip()}\n")


def log_event(paths: ScenarioPaths | None, event: str, **data: Any) -> None:
    entry = {"at": timestamp(), "event": event, **data}
    print(f"[{entry['at']}] {event}: {json.dumps(data, ensure_ascii=False)}", flush=True)
    if paths is not None:
        write_jsonl(paths.events_path, entry)


def prepare_wiki_export_fixture(work_dir: Path) -> None:
    """Create the wiki-export fixture with auth export service files and .wiki/ pages."""
    write(work_dir / "services/auth/exports.py", """\
from dataclasses import dataclass


@dataclass
class Session:
    user_id: str
    token: str


def auth_export_role(user_id: str) -> str:
    return "admin" if user_id.startswith("admin") else "user"
""")
    write(work_dir / "api/auth_routes.py", """\
from services.auth.exports import auth_export_role


def register_auth_export_routes(router):
    router.get("/api/auth/role/export", auth_export_role)
""")
    write(work_dir / "registry/export_registry.py", """\
EXPORT_REGISTRY = {
    "auth.role": "auth_export_role",
}
""")
    write(work_dir / "tests/test_auth_exports.py", """\
from services.auth.exports import auth_export_role
from registry.export_registry import EXPORT_REGISTRY


def test_auth_role_export_is_registered():
    assert auth_export_role("admin-1") == "admin"
    assert EXPORT_REGISTRY["auth.role"] == "auth_export_role"
""")
    write(work_dir / "README.md", """\
# Export Fixture

Auth exports are exposed through three synchronized places: service functions,
API route registration, and the central export registry. The local wiki records
this as a cross-cut operation so implementation can use it as a miss-prevention
map, then verify the current code before editing.
""")
    write(work_dir / "pytest.ini", """\
[pytest]
pythonpath = .
""")
    write(work_dir / ".wiki/index.md", """\
---
title: Wiki Index
description: Export fixture wiki navigation entry
tags: [index, wiki, export]
type: entity
summary: Links module and cross-cut pages for export implementation.
last_updated: 2026-05-07
---

# Wiki Index

## 模块（type: module）

- [[Modules/Auth exports]] — Auth export service contract and current naming.

## 跨模块同步改动（type: cross_cut）

- [[CrossCut/新增导出]] — 新增导出能力时必须同步检查 service、route、registry、tests。
""")
    write(work_dir / ".wiki/Modules/index.md", """\
---
title: Modules Index
description: Module wiki page index for export fixture
tags: [index, module, export]
type: entity
summary: Lists module notes for export fixture.
last_updated: 2026-05-07
---

# Modules Index

- [[Auth exports]] — Auth export service contract and current naming.
""")
    write(work_dir / ".wiki/Modules/Auth exports.md", """\
---
title: Auth exports
description: Auth service export naming and public contract
tags: [module, auth, exports]
type: module
summary: Auth exports use the `auth_export_*` prefix and are exposed through routes and registry entries.
last_updated: 2026-05-07
locators:
  - services/auth/exports.py
  - api/auth_routes.py
  - registry/export_registry.py
---

# Auth exports

Auth module exports live in `services/auth/exports.py` and use the `auth_export_*` prefix.
Public exports are wired through `api/auth_routes.py` and `registry/export_registry.py`.

相关 cross-cut：[[CrossCut/新增导出]]。
""")
    write(work_dir / ".wiki/CrossCut/index.md", """\
---
title: CrossCut Index
description: Cross-cut wiki page index for export fixture
tags: [index, cross-cut, export]
type: entity
summary: Lists cross-cut operation notes for export fixture.
last_updated: 2026-05-07
---

# CrossCut Index

- [[新增导出]] — 新增导出能力时必须同步检查 service、route、registry、tests。
""")
    write(work_dir / ".wiki/CrossCut/新增导出.md", """\
---
title: 新增导出
description: 新增导出函数时需要同步修改的位置和命名规则
tags: [cross-cut, exports, auth]
type: cross_cut
summary: 新增 auth 导出时同步检查 service function、API route、EXPORT_REGISTRY、pytest 覆盖。
last_updated: 2026-05-07
locators:
  - services/auth/exports.py
  - api/auth_routes.py
  - registry/export_registry.py
  - tests/test_auth_exports.py
---

# 新增导出

## 适用场景

当需求是"新增一个对外导出能力"时，用本页防漏；具体产品范围仍以 PRD 为准。

## 同步修改位置

- `services/auth/exports.py`：新增 `auth_export_*` service function 和必要的数据结构；本 fixture 的 session 导出函数名固定为 `auth_export_user_session`。
- `api/auth_routes.py`：在 `register_auth_export_routes` 里注册对应 HTTP path。
- `registry/export_registry.py`：在 `EXPORT_REGISTRY` 增加稳定 key 到函数名的映射；session 使用 `"auth.session": "auth_export_user_session"`。
- `tests/test_auth_exports.py`：覆盖函数行为、registry wiring 和 route wiring。

## 命名规则

Auth 模块沿用 `auth_export_<noun>`，registry key 沿用 `auth.<noun>`，route 沿用 `/api/auth/<noun>/export`。本 fixture 的 session 导出函数名固定为 `auth_export_user_session`，registry value 固定为 `auth_export_user_session`。

## 使用要求

Brainstorm 可在 PRD Technical Framing 中引用本页作为防漏入口，但必须写明核心 scope 和 fallback：若 wiki 与当前代码不一致，impl 调研代码逐一识别。
Impl 读取本页后必须验证路径和注册机制仍存在，再修改代码。

相关 module：[[Modules/Auth exports]]。
""")


def prepare_workdir(
    run_dir: Path,
    fixture: str,
    scenario_name: str,
    config: EnvConfig,
) -> ScenarioPaths:
    """Prepare workspace directory and return ScenarioPaths."""
    run_dir.mkdir(parents=True, exist_ok=True)
    work_dir = run_dir / "project"

    if fixture == "empty":
        work_dir.mkdir()
        (work_dir / ".gitkeep").write_text("", encoding="utf-8")
    elif fixture == "express-app":
        shutil.copytree(FIXTURE_DIR, work_dir)
    elif fixture == "wiki-export":
        work_dir.mkdir()
        prepare_wiki_export_fixture(work_dir)
    else:
        # Custom path
        fixture_path = Path(fixture)
        if not fixture_path.is_absolute():
            fixture_path = PLUGIN_ROOT / fixture
        shutil.copytree(fixture_path, work_dir)

    # Initialize git repo
    env = {
        "GIT_AUTHOR_NAME": "sdd-kit scenario",
        "GIT_AUTHOR_EMAIL": "scenario@example.invalid",
        "GIT_COMMITTER_NAME": "sdd-kit scenario",
        "GIT_COMMITTER_EMAIL": "scenario@example.invalid",
        "PATH": subprocess.check_output(
            ["bash", "-c", "echo $PATH"], text=True
        ).strip(),
    }
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "init"],
    ):
        subprocess.run(command, cwd=work_dir, env=env, check=True)

    paths = ScenarioPaths(
        run_dir=run_dir,
        work_dir=work_dir,
        transcript_path=run_dir / "transcript.jsonl",
        dialogue_path=run_dir / "dialogue.md",
        summary_path=run_dir / "summary.json",
        events_path=run_dir / "events.jsonl",
        test_report_path=work_dir / "test.md",
    )

    paths.dialogue_path.write_text(
        f"# Scenario dialogue — {scenario_name}\n\n"
        f"- 时间：{timestamp()}\n"
        f"- Model：{config.test_model}\n"
        f"- AI user model：{config.ai_user_model}\n\n",
        encoding="utf-8",
    )
    log_event(paths, "workdir_prepared", run_dir=str(run_dir), work_dir=str(work_dir))
    return paths
