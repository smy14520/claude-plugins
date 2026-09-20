"""测试 tinder-kit 技能与 Agent 的结构性契约。

验证点：
1. 技能双层分治：User-invoked 必须携带 disable-model-invocation: true；Model-invoked 必须允许模型调用。
2. 每个 SKILL.md 必须携带合法 frontmatter（name, description）。
3. 每个 Agent 必须携带合法 frontmatter（name, description）。
4. .claude-plugin/plugin.json 与 marketplace.json 声明一致性。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]

USER_INVOKED_FLOWS = {"init", "develop", "fix", "audit", "wayfinder", "teach", "dream"}
MODEL_INVOKED_DISCIPLINES = {
    "grilling",
    "codebase-design",
    "prototype",
    "domain-modeling",
    "tdd",
    "diagnose",
    "review",
    "architect",
    "wiki",
    "perceive",
}
BRIDGE_SKILLS = {"handoff"}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(content: str) -> dict[str, str | bool]:
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    out: dict[str, str | bool] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if v.lower() == "true":
                out[k] = True
            elif v.lower() == "false":
                out[k] = False
            else:
                out[k] = v
    return out


def test_plugin_manifest_valid():
    manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "tinder-kit"
    assert "version" in data
    # skills 和 agents 目录遵循 Claude Code 原生自动发现规范
    assert (PLUGIN_ROOT / "skills").is_dir()
    assert (PLUGIN_ROOT / "agents").is_dir()


def test_marketplace_registration():
    marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    assert marketplace_path.is_file()
    data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_names = [p["name"] for p in data.get("plugins", [])]
    assert "tinder-kit" in plugin_names
    assert "seed-kit" in plugin_names


def test_all_skills_have_required_frontmatter():
    skills_dir = PLUGIN_ROOT / "skills"
    assert skills_dir.is_dir()

    expected_all = USER_INVOKED_FLOWS | MODEL_INVOKED_DISCIPLINES | BRIDGE_SKILLS

    found_skills = set()
    for skill_folder in skills_dir.iterdir():
        if not skill_folder.is_dir() or skill_folder.name.startswith("."):
            continue
        skill_file = skill_folder / "SKILL.md"
        assert skill_file.is_file(), f"技能目录 {skill_folder.name} 缺少 SKILL.md"
        fm = _parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        assert "name" in fm, f"{skill_file} 缺少 name 字段"
        assert "description" in fm, f"{skill_file} 缺少 description 字段"
        found_skills.add(fm["name"])

    assert found_skills == expected_all, f"技能清单不一致，缺漏或冗余：{found_skills ^ expected_all}"


def test_user_invoked_flows_have_disable_model_invocation():
    skills_dir = PLUGIN_ROOT / "skills"
    for name in USER_INVOKED_FLOWS:
        skill_file = skills_dir / name / "SKILL.md"
        fm = _parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        assert fm.get("disable-model-invocation") is True, (
            f"User-invoked 编排流 {name} 必须包含 disable-model-invocation: true"
        )


def test_model_invoked_disciplines_allow_model_invocation():
    skills_dir = PLUGIN_ROOT / "skills"
    for name in MODEL_INVOKED_DISCIPLINES:
        skill_file = skills_dir / name / "SKILL.md"
        fm = _parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        assert fm.get("disable-model-invocation") is not True, (
            f"Model-invoked 原子素养 {name} 不得禁用模型调用"
        )


def test_all_agents_have_valid_frontmatter():
    agents_dir = PLUGIN_ROOT / "agents"
    assert agents_dir.is_dir()

    expected_agents = {"forge-impl", "forge-review", "forge-prototype"}
    found_agents = set()

    for agent_file in agents_dir.glob("*.md"):
        fm = _parse_frontmatter(agent_file.read_text(encoding="utf-8"))
        assert "name" in fm, f"{agent_file} 缺少 name"
        assert "description" in fm, f"{agent_file} 缺少 description"
        found_agents.add(fm["name"])

    assert found_agents == expected_agents, f"Agent 清单不一致：{found_agents ^ expected_agents}"
