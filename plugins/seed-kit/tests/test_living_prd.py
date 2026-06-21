"""generate_living_prd 的单元测试：config + 非 seed-kit 项目跳过。

living_prd_trigger.py 已移除——改用 hook 原生 async 直接调 generate_living_prd.py，
测试对象从 trigger 迁移到 generate。
"""
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
    """config enabled:true → 触发生成（无 prd.md 时 generate 会早退，但不因 enabled 阻断）。"""
    (tmp_path / ".arbor" / "tasks" / "demo").mkdir(parents=True)
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": True}}), encoding="utf-8"
    )
    r = run_generate(tmp_path)
    assert r.returncode == 0  # enabled 通过；无 prd.md 则 find_task 返回 None 早退，不报错


def test_config_disabled_skips(tmp_path: Path):
    """config enabled=false → 不生成 HTML。"""
    (tmp_path / ".arbor" / "tasks" / "demo").mkdir(parents=True)
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": False}}), encoding="utf-8"
    )
    r = run_generate(tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / ".arbor" / "artifacts" / "living-prd.html").exists()


def test_load_config_missing(tmp_path: Path):
    """无 config.json → 返回空（默认 enabled=true）。"""
    gen = _load_gen()
    assert gen._load_config(tmp_path) == {}


def test_load_config_enabled(tmp_path: Path):
    """正常 config → 返回 dict。"""
    gen = _load_gen()
    (tmp_path / ".arbor").mkdir()
    (tmp_path / ".arbor" / "config.json").write_text(
        json.dumps({"living_prd": {"enabled": True, "rate_limit_minutes": 10}}), encoding="utf-8"
    )
    cfg = gen._load_config(tmp_path)
    assert cfg["living_prd"]["enabled"] is True
    assert cfg["living_prd"]["rate_limit_minutes"] == 10


def test_load_config_malformed(tmp_path: Path):
    """config 损坏 → 返回空（用默认）。"""
    gen = _load_gen()
    (tmp_path / ".arbor").mkdir()
    (tmp_path / ".arbor" / "config.json").write_text("{bad json", encoding="utf-8")
    assert gen._load_config(tmp_path) == {}
