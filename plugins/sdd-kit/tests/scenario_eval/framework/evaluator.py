"""AI evaluator: scores scenario run artifacts using Anthropic API."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DimensionScore:
    name: str
    score: int  # 1-5
    reasoning: str
    weight: float = 1.0


@dataclass
class EvaluationResult:
    dimensions: list[DimensionScore]
    total_score: float  # weighted average
    summary: str
    raw_response: str


class Evaluator:
    """Evaluates scenario run artifacts using Claude API."""

    def __init__(self, api_key: str, model: str, base_url: str = ""):
        import anthropic
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = anthropic.Anthropic(**kwargs)
        self.model = model

    def evaluate(
        self,
        artifacts: dict[str, str],  # {"prd": ..., "diff": ..., "task_json": ..., "user_request": ...}
        dimensions: list[dict[str, Any]],  # [{"name": ..., "prompt": ..., "weight": ...}]
        scenario_context: str = "",
    ) -> EvaluationResult:
        """Evaluate artifacts against given dimensions. Returns scores 1-5 per dimension."""
        prompt = self._build_prompt(artifacts, dimensions, scenario_context)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract text from response, skipping ThinkingBlocks
        raw = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw = block.text
                break
        return self._parse_response(raw, dimensions)

    def _build_prompt(
        self,
        artifacts: dict[str, str],
        dimensions: list[dict[str, Any]],
        scenario_context: str,
    ) -> str:
        sections = []
        sections.append("你是一个 AI 代码质量评估员。请根据以下产物和评估维度打分。")
        sections.append("")
        if scenario_context:
            sections.append(f"## 场景背景\n\n{scenario_context}")
            sections.append("")
        if artifacts.get("user_request"):
            sections.append(f"## 用户需求\n\n{artifacts['user_request']}")
            sections.append("")
        if artifacts.get("prd"):
            prd_text = artifacts["prd"]
            if len(prd_text) > 15000:
                prd_text = prd_text[:15000] + "\n\n[... truncated ...]"
            sections.append(f"## PRD\n\n{prd_text}")
            sections.append("")
        if artifacts.get("task_json"):
            sections.append(f"## task.json\n\n```json\n{artifacts['task_json']}\n```")
            sections.append("")
        if artifacts.get("source_files"):
            source_text = artifacts["source_files"]
            if len(source_text) > 80000:
                source_text = source_text[:80000] + "\n\n[... truncated ...]"
            sections.append(f"## 项目源代码\n\n{source_text}")
            sections.append("")
        elif artifacts.get("diff"):
            diff_text = artifacts["diff"]
            if len(diff_text) > 30000:
                diff_text = diff_text[:30000] + "\n\n[... truncated ...]"
            sections.append(f"## 代码 Diff\n\n```diff\n{diff_text}\n```")
            sections.append("")

        sections.append("## 评估维度")
        sections.append("")
        for i, dim in enumerate(dimensions, 1):
            sections.append(f"{i}. **{dim['name']}** (权重 {dim.get('weight', 1.0)}): {dim['prompt']}")
        sections.append("")
        sections.append("## 输出格式")
        sections.append("")
        sections.append("请严格按以下 JSON 格式输出（不要包含其他文字）：")
        sections.append("")
        sections.append("```json")
        sections.append(json.dumps({
            "dimensions": [
                {"name": "dimension_name", "score": 4, "reasoning": "简短理由"}
            ],
            "summary": "一句话总结"
        }, ensure_ascii=False, indent=2))
        sections.append("```")
        sections.append("")
        sections.append("分数标准：1=完全不满足 2=严重不足 3=基本满足但有明显问题 4=良好 5=优秀")
        return "\n".join(sections)

    def _parse_response(self, raw: str, dimensions: list[dict[str, Any]]) -> EvaluationResult:
        """Parse the JSON response from the evaluator."""
        # Extract JSON from response (may be wrapped in ```json ... ```)
        json_str = raw
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            json_str = raw[start:end].strip()
        elif "```" in raw:
            start = raw.index("```") + 3
            end = raw.index("```", start)
            json_str = raw[start:end].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: return zeros with error
            return EvaluationResult(
                dimensions=[
                    DimensionScore(name=d["name"], score=0, reasoning="Failed to parse evaluator response", weight=d.get("weight", 1.0))
                    for d in dimensions
                ],
                total_score=0.0,
                summary="Evaluation parse error",
                raw_response=raw,
            )

        dim_scores = []
        weight_map = {d["name"]: d.get("weight", 1.0) for d in dimensions}
        for item in data.get("dimensions", []):
            name = item.get("name", "unknown")
            dim_scores.append(DimensionScore(
                name=name,
                score=int(item.get("score", 0)),
                reasoning=item.get("reasoning", ""),
                weight=weight_map.get(name, 1.0),
            ))

        # Calculate weighted average
        total_weight = sum(d.weight for d in dim_scores) or 1.0
        total_score = sum(d.score * d.weight for d in dim_scores) / total_weight

        return EvaluationResult(
            dimensions=dim_scores,
            total_score=round(total_score, 2),
            summary=data.get("summary", ""),
            raw_response=raw,
        )


def _collect_source_files(work_dir: Path, max_total_chars: int = 80000) -> str:
    """Collect source files from project directory for evaluation."""
    extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".yml", ".yaml",
                  ".css", ".html", ".prisma", ".sql", ".md"}
    skip_dirs = {"node_modules", ".git", "dist", "build", ".arbor", "test-results"}
    skip_names = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

    files: list[tuple[str, str]] = []
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        if path.name in skip_names:
            continue
        if any(part in skip_dirs for part in path.relative_to(work_dir).parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(work_dir))
            files.append((rel, content))
        except (UnicodeDecodeError, OSError):
            continue

    # Build output, respecting max size
    output_parts: list[str] = []
    total = 0
    for rel, content in files:
        entry = f"### {rel}\n\n```\n{content}\n```\n"
        if total + len(entry) > max_total_chars:
            output_parts.append(f"\n[... {len(files) - len(output_parts)} more files truncated ...]")
            break
        output_parts.append(entry)
        total += len(entry)

    return "\n".join(output_parts)


def evaluate_run(
    run_dir: Path,
    dimensions: list[dict[str, Any]],
    api_key: str,
    model: str,
    scenario_context: str = "",
    base_url: str = "",
) -> EvaluationResult:
    """Convenience function: load artifacts from a run directory and evaluate."""
    work_dir = run_dir / "project"
    artifacts: dict[str, str] = {}

    # Load PRD
    prd_candidates = list(work_dir.glob(".arbor/tasks/*/prd.md"))
    if prd_candidates:
        artifacts["prd"] = prd_candidates[0].read_text(encoding="utf-8")

    # Load task.json
    task_candidates = list(work_dir.glob(".arbor/tasks/*/task.json"))
    if task_candidates:
        artifacts["task_json"] = task_candidates[0].read_text(encoding="utf-8")

    # Load project source files instead of diff
    source_content = _collect_source_files(work_dir)
    if source_content:
        artifacts["source_files"] = source_content

    # Load user request from summary
    summary_path = run_dir / "summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            artifacts["user_request"] = summary.get("user_request", "")
        except (json.JSONDecodeError, KeyError):
            pass

    evaluator = Evaluator(api_key=api_key, model=model, base_url=base_url)
    return evaluator.evaluate(artifacts, dimensions, scenario_context)
