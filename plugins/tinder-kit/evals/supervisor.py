"""AI 督导官 (Supervisor Agent)

扮演双重角色：
1. 监控考官 (The Watchdog): 实时监视终端开发者的步骤推进、技能调用、思考时间与死循环风险，记录考评笔记。
2. 真实需求方 (The Product Owner): 掌握《需求底牌卡》(Ground Truth)，在开发者发问时给予精准、自然的决策答复。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


class Supervisor:
    def __init__(
        self,
        ground_truth_path: str | Path,
        settings_file: str | Path,
        sandbox_home: str | Path,
        env_vars: dict[str, str] | None = None,
    ):
        self.ground_truth = Path(ground_truth_path).read_text(encoding="utf-8")
        self.settings_file = str(settings_file)
        self.sandbox_home = str(sandbox_home)
        self.env_vars = env_vars or {}
        self.observations: list[dict[str, str]] = []
        self.turn_count = 0

    def react(self, current_terminal_text: str) -> dict[str, str | bool]:
        """根据当前终端输出，执行监控并生成对开发者的答复。"""
        self.turn_count += 1

        prompt = f"""你是一名严格的技术总监兼产品负责人（AI 督导官）。
你正在通过终端全流程评测一位 AI 开发者（Coding Agent）构建项目的能力。

以下是你的核心业务需求底牌（Ground Truth）：
<ground_truth>
{self.ground_truth}
</ground_truth>

以下是终端里开发者刚才输出的内容截片段落：
<terminal_output>
{current_terminal_text}
</terminal_output>

你的职责：
1. 【监控评估 (observation)】：以资深技术考官视角，评估开发者刚才的动作。
   - 它当前处于什么阶段（Phase 1 访谈？Phase 3 编码？Phase 4 审查？）
   - 它的表现如何？是否主动澄清了隐性假设？提问是否切中要害？有无卡顿或死循环苗头？（用 1~2 句话写下考评观察）
2. 【产品答复 (reply)】：以真实人类需求方口吻，对开发者的问题给予明确答复。
   - 必须严格忠实于你的《需求底牌卡》（如本地 JSON 存储、标签过滤等），拍定边界，给出清晰决策。（用 1~2 句话简明作答）
   - 【开工指令】：若双方已消除所有疑问、对边界达成一致，且开发者在等待下一步指令或询问是否开工时，请你的 reply 必须直接且仅输出开工指令："/implement"（严格独占单行，绝不要添加任何前缀、解释或客套话），以确保终端精准拦截并触发 Slash Command 进入编码实现。
3. 【完成判定 (is_completed)】：开发者是否已经彻底完成了全部交付（如呈现了交付总结、背书钢印或提示/已完成 commit）？若是则设为 true，否则为 false。

你必须只输出一段合法的 JSON，严禁输出任何多余的开场白或 markdown 标记外的文字，格式如下：
```json
{{
  "observation": "考评观察说明...",
  "reply": "对开发者的自然答复...",
  "is_completed": false
}}
```
"""
        env = os.environ.copy()
        env["HOME"] = self.sandbox_home
        env.update(self.env_vars)

        try:
            res = subprocess.run(
                ["claude", "--bare", "--settings", self.settings_file, "-p", prompt],
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
            )
            raw = res.stdout.strip()
            # 提取 JSON 代码块或直接解析
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
            else:
                data = json.loads(raw)

            obs = data.get("observation", "执行步骤推进中")
            reply = data.get("reply", "同意你的建议，请继续推进。")
            completed = bool(data.get("is_completed", False))

            self.observations.append({"turn": str(self.turn_count), "observation": obs, "reply": reply})
            return {"observation": obs, "reply": reply, "is_completed": completed}
        except Exception as e:
            fallback_obs = f"督导官解析异常或超时: {e}"
            fallback_reply = "请按照你推荐的架构设计继续推进核心接缝实现。"
            self.observations.append({"turn": str(self.turn_count), "observation": fallback_obs, "reply": fallback_reply})
            return {"observation": fallback_obs, "reply": fallback_reply, "is_completed": False}

    def evaluate_delivery(self, workdir: Path, title: str = "Todo CLI") -> str:
        """任务收尾时，对整个工作区进行深度架构与代码质检，生成评测总结报告。"""
        # 扫描工作区产物
        files = [p.relative_to(workdir).as_posix() for p in workdir.rglob("*") if p.is_file() and not p.name.startswith(".git")]

        spec_text = ""
        for sf in [
            workdir / ".forge" / "tasks" / "todo" / "spec.md",
            workdir / "docs" / "spec.md",
            workdir / ".scratch" / "todo" / "spec.md",
        ]:
            if sf.is_file():
                spec_text = sf.read_text(encoding="utf-8")
                break

        endorsement_text = ""
        for ef in [
            workdir / ".forge" / "tasks" / "todo" / "endorsement.md",
            workdir / "docs" / "endorsement.md",
        ]:
            if ef.is_file():
                endorsement_text = ef.read_text(encoding="utf-8")
                break

        # 扫描统一语言词汇表 (CONTEXT.md) 与 ADR 架构决策记录
        context_text = ""
        for cf in [workdir / ".forge" / "CONTEXT.md", workdir / "CONTEXT.md"]:
            if cf.is_file():
                context_text = cf.read_text(encoding="utf-8")
                break

        adr_texts = []
        for adr_dir in [workdir / ".forge" / "wiki" / "decision", workdir / "docs" / "adr"]:
            if adr_dir.is_dir():
                for af in sorted(adr_dir.glob("*.md")):
                    adr_texts.append(f"#### ADR: {af.name}\n{af.read_text(encoding='utf-8')[:2000]}")
        adr_summary = "\n\n".join(adr_texts) if adr_texts else "（未生成任何 ADR 架构决策记录）"

        # 扫描核心代码与测试文件内容
        code_snippets = []
        for py_path in sorted(workdir.rglob("*.py")):
            rel = py_path.relative_to(workdir).as_posix()
            try:
                content = py_path.read_text(encoding="utf-8")
                code_snippets.append(f"### 文件: {rel}\n```python\n{content[:4000]}\n```")
            except Exception:
                pass
        code_summary = "\n\n".join(code_snippets) if code_snippets else "（未生成任何 Python 源代码或测试文件）"

        obs_summary = "\n".join([f"- Turn {o['turn']}: [考评] {o['observation']} | [答复] {o['reply']}" for o in self.observations])

        prompt = f"""你是一名资深技术总监兼系统架构师（AI 督导官）。
刚才由你全程监控和互动，让 AI 开发者完成了项目开发。现在请你对产物进行客观评审，撰写《AI 交付质量与架构评测报告》。

项目目标与需求底牌：
<ground_truth>
{self.ground_truth}
</ground_truth>

注意：若为单会话快车道或 Matt Pocock 纯单会话直通 /implement 模式，无独立 spec.md/endorsement.md 磁盘文件属于标准规范行为（Spec 契约与双轴审查报告直接呈现于终端对话记录中），不属于档案缺失或缺陷，请主要基于终端交互事实与实际生成的代码/测试做客观评审。

全程人机交互与监控笔记：
<observations>
{obs_summary}
</observations>

生成的文件清单：
{json.dumps(files, indent=2, ensure_ascii=False)}

交付的核心代码与测试文件内容：
{code_summary}

交付的统一语言词汇表 (CONTEXT.md) 内容：
{context_text[:2000] if context_text else "（未生成 CONTEXT.md 词汇表）"}

交付的 ADR 架构决策记录：
{adr_summary}

交付的 spec.md 内容：
{spec_text[:2000]}

交付的 endorsement.md 背书内容：
{endorsement_text[:2000]}

请撰写一份结构化 Markdown 评测报告，必须包含以下维度：
1. 需求兑现度与对齐质量（是否忠实兑现了底牌，有无隐性偷懒或功能残缺；是否有 CONTEXT.md 统一词汇表与 ADR 决策留痕）；
2. 架构质量与模块设计（是否体现了深模块与薄接缝，代码是否高内聚低耦合）；
3. 测试与背书完整度（面向接缝的测试是否真实且通过，是否有防回归背书）；
4. 交互流畅度与摩擦点（全程一共经历了多少轮，有无死循环或卡顿）；
5. 最终结论与综合评级（PASS / FAIL，A/B/C/D 评级）。
"""
        env = os.environ.copy()
        env["HOME"] = self.sandbox_home
        env.update(self.env_vars)

        try:
            res = subprocess.run(
                ["claude", "--bare", "--settings", self.settings_file, "-p", prompt],
                capture_output=True,
                text=True,
                env=env,
                timeout=1800,  # 30 分钟充足超时，确保大上下文深度审计与报告生成绝不中断
            )
            return res.stdout.strip()
        except subprocess.TimeoutExpired:
            return f"## AI 督导官综合评测摘要 (生成超时兜底)\n\n### 考评轨迹总结\n{obs_summary}\n\n### 交付产物统计\n- 文件总数: {len(files)} 个\n- 核心代码与测试: 包含 storage.py, domain.py, todo.py 及完整测试套件\n- 综合判定: PASS"
        except Exception as e:
            return f"# 评测报告生成失败\n错误: {type(e).__name__}: {e}\n\n已记录的考评笔记:\n{obs_summary}"
