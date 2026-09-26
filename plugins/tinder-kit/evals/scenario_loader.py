"""场景加载与自发现机制 (Scenario Loader)

负责将声明式的 SCENARIO.md 解析为结构化的 Scenario 实体。
支持自发现、YAML Frontmatter 解析、Markdown 底牌与主观审美基准拆解。
兼容旧版 prompt.txt + ground_truth.md 目录。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class Scenario:
    slug: str
    scenario_dir: Path
    name: str
    description: str
    scenario_type: str  # "e2e" or "single-skill"
    prompt: str
    ground_truth: str
    supervisor_taste: str
    setup_project: bool = True
    max_turns: int = 30
    initial_commands: dict[str, str] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def get_initial_cmd(self, arm_name: str) -> str:
        """根据当前运行组别解析启动指令。"""
        # 1. 显式按组命中的指令
        if arm_name in self.initial_commands:
            return self.initial_commands[arm_name]
        if "default" in self.initial_commands:
            return self.initial_commands["default"]

        # 2. 单技能场景且有 initial_command
        if "initial_command" in self.metadata:
            return str(self.metadata["initial_command"])

        # 3. 端到端常规推导
        p = self.prompt.strip()
        if not p:
            p = self.name

        if arm_name in ["tinder_develop", "treatment_tinder_kit"]:
            return f'/develop "{p}"'
        elif arm_name in ["tinder_manual", "mattpocock_skills"]:
            return f'/grill-with-docs "{p}"'
        else:
            return p


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_scenario_md(slug: str, scenario_dir: Path, file_path: Path) -> Scenario:
    text = file_path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if m:
        fm_text, body = m.group(1), m.group(2)
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception:
            fm = {}
    else:
        fm = {}
        body = text

    name = fm.get("name", slug)
    desc = fm.get("description", "")
    stype = fm.get("type", "e2e")
    prompt = fm.get("prompt", "")
    setup_project = bool(fm.get("setup_project", True))
    max_turns = int(fm.get("max_turns", 30))
    initial_commands = fm.get("commands", {}) or {}
    if "initial_command" in fm and not initial_commands:
        initial_commands["default"] = fm["initial_command"]

    # 从 body 中拆解 Ground Truth 与 Supervisor Taste / Focus
    sections = re.split(r"\n(?=#\s+)", "\n" + body.strip())
    gt_parts = []
    taste_parts = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        first_line = sec.split("\n", 1)[0].lower()
        if any(k in first_line for k in ["taste", "focus", "督导官", "审美", "人设", "persona", "品味"]):
            taste_parts.append(sec)
        else:
            gt_parts.append(sec)

    ground_truth = "\n\n".join(gt_parts).strip() if gt_parts else body.strip()
    supervisor_taste = "\n\n".join(taste_parts).strip() if taste_parts else ""

    # 如果 prompt 为空，尝试寻找首段或 prompt.txt
    if not prompt:
        p_file = scenario_dir / "prompt.txt"
        if p_file.is_file():
            prompt = p_file.read_text(encoding="utf-8").strip()
        else:
            prompt = desc or name

    return Scenario(
        slug=slug,
        scenario_dir=scenario_dir,
        name=name,
        description=desc,
        scenario_type=stype,
        prompt=prompt,
        ground_truth=ground_truth,
        supervisor_taste=supervisor_taste,
        setup_project=setup_project,
        max_turns=max_turns,
        initial_commands=initial_commands,
        metadata=fm,
    )


def load_legacy_scenario(slug: str, scenario_dir: Path) -> Scenario:
    prompt_file = scenario_dir / "prompt.txt"
    prompt = prompt_file.read_text(encoding="utf-8").strip() if prompt_file.is_file() else ""
    gt_file = scenario_dir / "ground_truth.md"
    gt = gt_file.read_text(encoding="utf-8").strip() if gt_file.is_file() else prompt
    return Scenario(
        slug=slug,
        scenario_dir=scenario_dir,
        name=slug,
        description="",
        scenario_type="e2e",
        prompt=prompt,
        ground_truth=gt,
        supervisor_taste="",
        setup_project=True,
        max_turns=30,
        initial_commands={},
        metadata={},
    )


def load_scenario(identifier: str, scenarios_root: Path) -> Scenario:
    """根据标识符加载场景，支持相对路径、绝对路径、目录名或常用别名。"""
    target_path = Path(identifier)
    if target_path.is_dir():
        scenario_dir = target_path.resolve()
        slug = scenario_dir.name
    elif (scenarios_root / identifier).is_dir():
        scenario_dir = (scenarios_root / identifier).resolve()
        slug = identifier
    else:
        alias_map = {
            "small": "small-due",
            "medium": "todo-cli",
            "todo": "todo-cli",
            "large": "large-wiki",
            "greenfield": "greenfield-mock",
        }
        mapped = alias_map.get(identifier.lower())
        if mapped and (scenarios_root / mapped).is_dir():
            scenario_dir = (scenarios_root / mapped).resolve()
            slug = mapped
        else:
            available = [
                p.name for p in scenarios_root.iterdir()
                if p.is_dir() and not p.name.startswith((".", "_"))
            ]
            raise FileNotFoundError(
                f"未找到场景 '{identifier}'。\n已发现的可用场景目录: {', '.join(sorted(available))}"
            )

    scenario_file = scenario_dir / "SCENARIO.md"
    if scenario_file.is_file():
        return parse_scenario_md(slug, scenario_dir, scenario_file)
    else:
        return load_legacy_scenario(slug, scenario_dir)


def list_available_scenarios(scenarios_root: Path) -> list[dict[str, str]]:
    """列出当前 scenarios 目录下所有已就绪的场景。"""
    scenarios = []
    if not scenarios_root.is_dir():
        return scenarios

    for p in sorted(scenarios_root.iterdir()):
        if not p.is_dir() or p.name.startswith((".", "_")):
            continue
        try:
            sc = load_scenario(p.name, scenarios_root)
            scenarios.append({
                "slug": sc.slug,
                "name": sc.name,
                "type": sc.scenario_type,
                "description": sc.description,
            })
        except Exception:
            scenarios.append({"slug": p.name, "name": p.name, "type": "unknown", "description": ""})
    return scenarios
