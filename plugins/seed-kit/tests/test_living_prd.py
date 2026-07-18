"""generate_living_prd 的单元测试：opt-in、跳过条件与真实 HTML 生成。"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

GENERATE = Path(__file__).resolve().parents[1] / "hooks" / "generate_living_prd.py"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def run_generate(cwd: Path) -> subprocess.CompletedProcess:
    env = {"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "PATH": "/usr/bin:/bin"}
    return subprocess.run(
        [sys.executable, str(GENERATE)], cwd=str(cwd),
        capture_output=True, text=True, env=env,
    )


def _load_gen():
    spec = importlib.util.spec_from_file_location("generate_living_prd", GENERATE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_non_seed_kit_skipped(tmp_path: Path):
    """无 .arbor/tasks → 不生成 HTML。"""
    r = run_generate(tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / ".arbor" / "artifacts" / "living-prd.html").exists()


def test_opt_in_default_off(tmp_path: Path):
    """opt-in：有 .arbor/tasks 但无 config → 默认不生成（要 enabled:true 才生成）。"""
    (tmp_path / ".arbor" / "tasks" / "demo").mkdir(parents=True)
    # 无 config.json
    r = run_generate(tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / ".arbor" / "artifacts" / "living-prd.html").exists()


def test_opt_in_enabled_generates(tmp_path: Path):
    """config enabled:true + 有效 PRD → 生成固定位置的 HTML。"""
    task_dir = tmp_path / ".arbor" / "tasks" / "demo"
    task_dir.mkdir(parents=True)
    (task_dir / "prd.md").write_text(
        """# Demo Product

## Goal

验证 Living PRD 的真实生成路径。

## Acceptance Criteria

### [ ] S-001 Render status

* [ ] 显示当前 slice。

## Out of Scope

* 不测试浏览器展示。
""",
        encoding="utf-8",
    )
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": True}}), encoding="utf-8"
    )

    r = run_generate(tmp_path)

    assert r.returncode == 0
    output = tmp_path / ".arbor" / "artifacts" / "living-prd.html"
    assert output.is_file()
    rendered = output.read_text(encoding="utf-8")
    assert "Demo Product" in rendered
    assert "demo" in rendered
    assert "S-001" in rendered


def test_config_disabled_skips(tmp_path: Path):
    """config enabled=false → 不生成 HTML。"""
    (tmp_path / ".arbor" / "tasks" / "demo").mkdir(parents=True)
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": False}}), encoding="utf-8"
    )
    r = run_generate(tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / ".arbor" / "artifacts" / "living-prd.html").exists()


def test_invalid_config_shapes_skip(tmp_path: Path):
    """合法 JSON 但 schema 错误或 enabled 非 true → 安全跳过。"""
    invalid_configs = [
        [],
        {"living_prd": []},
        {"living_prd": {"enabled": "true"}},
        {"living_prd": {"enabled": 1}},
    ]
    for index, config in enumerate(invalid_configs):
        root = tmp_path / str(index)
        task_dir = root / ".arbor" / "tasks" / "demo"
        task_dir.mkdir(parents=True)
        (task_dir / "prd.md").write_text(
            "# Demo\n\n## Acceptance Criteria\n\n### [ ] S-001 Demo\n",
            encoding="utf-8",
        )
        (root / ".arbor" / "config.json").write_text(json.dumps(config), encoding="utf-8")

        r = run_generate(root)

        assert r.returncode == 0
        assert not (root / ".arbor" / "artifacts" / "living-prd.html").exists()


def test_load_config_missing(tmp_path: Path):
    """无 config.json → 返回空，由调用方按默认关闭处理。"""
    gen = _load_gen()
    assert gen._load_config(tmp_path) == {}


def test_load_config_enabled(tmp_path: Path):
    """正常 config → 返回 enabled 配置。"""
    gen = _load_gen()
    (tmp_path / ".arbor").mkdir()
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": True}}), encoding="utf-8"
    )
    cfg = gen._load_config(tmp_path)
    assert cfg == {"living_prd": {"enabled": True}}


def test_load_config_malformed(tmp_path: Path):
    """config 损坏 → 返回空（用默认）。"""
    gen = _load_gen()
    (tmp_path / ".arbor").mkdir()
    (tmp_path / ".arbor" / "config.json").write_text("{bad json", encoding="utf-8")
    assert gen._load_config(tmp_path) == {}
