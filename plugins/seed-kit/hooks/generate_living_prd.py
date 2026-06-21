#!/usr/bin/env python3
"""generate_living_prd.py — Living PRD HTML 生成器（Python 版）。

数据源：`seed status <task> --json`（结构化，不靠 sed 猜段落）+ prd.md + review.md + git log。
输出：.arbor/artifacts/living-prd.html（自包含、内联 CSS/JS、dashboard 风格）。

设计原则：清晰来自模板设计，不靠 LLM；机械填结构化数据即可达到 dashboard 清晰度。
零侵入：只读 prd/slices/evidence/review，不改任何状态；HTML 是 derived（可删可重生）。
"""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

STATE_META = {
    "passed": ("✅", "ok"),
    "failed": ("❌", "fail"),
    "recorded": ("📝", "rec"),
    "missing": ("⬜", "miss"),
}
KIND_LABEL = {"assert": "断言", "judge": "裁决", "human": "签收"}


def _project_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return Path.cwd()


def _find_task(root: Path) -> tuple[str, Path] | None:
    prds = sorted((root / ".arbor" / "tasks").glob("*/prd.md"))
    if not prds:
        return None
    return prds[0].parent.name, prds[0]


def _run_seed_status(root: Path, task: str, plugin_root: str) -> dict | None:
    """优先用 PATH 里的 seed，回退到 plugin 的 seed.py。"""
    candidates = [
        ["seed", "status", task, "--json"],
        ["python3", str(Path(plugin_root) / "tools" / "seed.py"), "status", task, "--json"],
    ]
    for cmd in candidates:
        try:
            r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=30)
            # seed status 带 errors 时仍 exit 1，但 stdout 是有效 JSON；只看能否解析
            if r.stdout.strip():
                try:
                    return json.loads(r.stdout)
                except json.JSONDecodeError:
                    continue
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            continue
    return None


def _git_log(root: Path, prd: Path) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "log", "--date=short", "--format=%h|%ad|%s", "-15", "--", str(prd)],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        return [ln for ln in r.stdout.splitlines() if ln.strip()] if r.returncode == 0 else []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _prd_title(prd: Path) -> str:
    for line in prd.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return prd.parent.name


def _metrics(status: dict) -> dict:
    slices = status.get("slices", [])
    total = len(slices)
    done = sum(1 for s in slices if s.get("done"))
    all_checks = [c for s in slices for c in s.get("checks", [])]
    passed = sum(1 for c in all_checks if c.get("state") == "passed")
    missing = sum(1 for c in all_checks if c.get("state") == "missing")
    verdicts = sum(1 for c in all_checks if c.get("kind") == "judge")
    rate = round(passed / len(all_checks) * 100) if all_checks else 0
    progress = round(done / total * 100) if total else 0
    return {
        "total": total, "done": done, "pending": total - done,
        "checks": len(all_checks), "passed": passed, "missing": missing,
        "verdicts": verdicts, "rate": rate, "progress": progress,
    }


def _badge(state: str) -> str:
    icon, cls = STATE_META.get(state, ("❓", "miss"))
    return f'<span class="badge {cls}">{icon} {state}</span>'


def _check_row(check: dict) -> str:
    kind = check.get("kind", "?")
    oid = check.get("obligation_id") or "(legacy)"
    surfaces = ", ".join(check.get("surfaces", [])) or "—"
    state = check.get("state", "missing")
    target = html.escape(str(check.get("target", ""))[:90])
    score = ""
    summary = check.get("score_summary")
    if isinstance(summary, dict):
        avg = summary.get("average")
        if avg is not None:
            score = f'<span class="score">score {avg}</span>'
    verdict = check.get("verdict")
    vbadge = f'<span class="vbadge">verdict {verdict}</span>' if verdict else ""
    return f"""<div class="check">
      <span class="ckind {kind}">{kind}</span>
      <span class="csurf">{html.escape(surfaces)}</span>
      <code class="coid">{html.escape(str(oid))}</code>
      <span class="ctarget">{target}</span>
      <span class="cstate">{_badge(state)}</span>
      {score}{vbadge}
    </div>"""


def _slice_card(sl: dict) -> str:
    sid = sl.get("id", "?")
    title = html.escape(sl.get("title", ""))
    done = sl.get("done")
    checks = sl.get("checks", [])
    passed = sum(1 for c in checks if c.get("state") == "passed")
    mark = "☑" if done else "☐"
    cls = "done" if done else ("todo" if passed == 0 and all(c.get("state") == "missing" for c in checks) else "wip")
    rows = "".join(_check_row(c) for c in checks) or '<div class="check empty">（无验证项）</div>'
    return f"""<details class="slice {cls}"{' open' if not done else ''}>
      <summary><span class="smark">{mark}</span> <code>{html.escape(sid)}</code> {title}
        <span class="scount">{passed}/{len(checks)}</span></summary>
      <div class="checks">{rows}</div>
    </details>"""


CSS = """
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--fg:#e6edf3;--muted:#8b949e;
--accent:#58a6ff;--ok:#3fb950;--fail:#f85149;--warn:#d29922;--rec:#8b949e;--miss:#484f58}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font-family:-apple-system,'Segoe UI',sans-serif;line-height:1.5}
.wrap{max-width:1000px;margin:0 auto;padding:24px 16px 64px}
.header{background:linear-gradient(135deg,#1f6feb33,#23863622);border:1px solid var(--border);
border-radius:12px;padding:20px 24px;margin-bottom:20px}
.header h1{margin:0;font-size:20px}.header .sub{color:var(--muted);font-size:13px;margin-top:4px}
.header .branch{display:inline-block;background:var(--card);border:1px solid var(--border);
border-radius:6px;padding:2px 8px;font-size:12px;margin-left:8px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px}
.metric{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.metric .v{font-size:26px;font-weight:700;color:var(--accent)}.metric .l{color:var(--muted);font-size:12px;margin-top:2px}
.progress{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:20px}
.progress .top{display:flex;justify-content:space-between;margin-bottom:8px;font-size:14px}
.bar{height:10px;background:var(--bg);border-radius:5px;overflow:hidden}
.fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--ok));transition:width .4s}
.section{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px}
.section h2{margin:0 0 12px;font-size:15px;color:var(--muted)}
.slice{border:1px solid var(--border);border-radius:8px;margin-bottom:8px;background:var(--bg);overflow:hidden}
.slice[open]{border-color:var(--accent)}
.slice summary{cursor:pointer;padding:10px 14px;display:flex;align-items:center;gap:8px;font-size:14px;list-style:none}
.slice summary::-webkit-details-marker{display:none}
.slice .smark{font-size:16px}.slice code{color:var(--accent);font-size:12px}
.slice .scount{margin-left:auto;background:var(--card);border:1px solid var(--border);
border-radius:10px;padding:1px 8px;font-size:11px;color:var(--muted)}
.slice.done summary{color:var(--muted)}.slice.wip{border-left:3px solid var(--warn)}
.checks{padding:6px 14px 12px;border-top:1px solid var(--border)}
.check{display:flex;align-items:center;gap:8px;padding:5px 0;font-size:12px;flex-wrap:wrap}
.ckind{font-size:10px;padding:1px 6px;border-radius:4px;font-weight:600;text-transform:uppercase}
.ckind.assert{background:#1f6feb33;color:var(--accent)}.ckind.judge{background:#8957e533;color:#bc8cff}
.ckind.human{background:#d2992233;color:var(--warn)}
.csurf{color:var(--muted)}.coid{color:var(--muted);font-size:11px}.ctarget{flex:1;min-width:120px;color:var(--fg)}
.badge{font-size:10px;padding:1px 7px;border-radius:10px;font-weight:600}
.badge.ok{background:#23863633;color:var(--ok)}.badge.fail{background:#f8514933;color:var(--fail)}
.badge.rec{background:#8b949e33;color:var(--rec)}.badge.miss{background:#484f5833;color:var(--miss)}
.score{background:#8957e533;color:#bc8cff;font-size:10px;padding:1px 7px;border-radius:10px}
.vbadge{background:#23863633;color:var(--ok);font-size:10px;padding:1px 7px;border-radius:10px}
.tl{font-size:12px;color:var(--muted)}.tl .row{padding:3px 0;border-bottom:1px solid var(--border)}
.tl .row:last-child{border:0}.tl code{color:var(--accent)}
.empty{color:var(--muted);font-style:italic;padding:8px 0}
.foot{text-align:center;color:var(--miss);font-size:11px;margin-top:24px}
@media(max-width:640px){.wrap{padding:12px}.check{font-size:11px}}
"""


def render(task: str, title: str, status: dict, review: str, git_log: list[str], branch: str, generated: str) -> str:
    m = _metrics(status)
    slices = status.get("slices", [])
    next_id = status.get("next")
    slice_html = "".join(_slice_card(s) for s in slices) or '<div class="empty">（无 slice）</div>'
    next_html = f'<div class="empty">下一个：{html.escape(str(next_id))}</div>' if next_id else ""
    tl_html = "".join(
        f'<div class="row"><code>{p[0]}</code> <span>{p[1]}</span> {html.escape(p[2]) if len(p) > 2 else ""}</div>'
        for p in (r.split("|", 2) for r in git_log)
    ) or '<div class="empty">（无 git 历史）</div>'
    review_html = f'<pre class="review">{html.escape(review[:2000])}</pre>' if review else '<div class="empty">（暂无 review.md）</div>'
    review_sec = '<div class="section"><h2>🔍 Review</h2>{}</div>'.format(review_html) if review else ""
    return f"""<!doctype html><html lang="zh"><meta charset="utf-8">
<title>Living PRD — {html.escape(title)}</title>
<style>{CSS}</style>
<div class="wrap">
  <div class="header">
    <h1>🌱 Living PRD · {html.escape(title)}</h1>
    <div class="sub">task <code>{html.escape(task)}</code> · 生成于 {generated}
      <span class="branch">{html.escape(branch)}</span></div>
  </div>
  <div class="metrics">
    <div class="metric"><div class="v">{m['total']}</div><div class="l">总 Slices</div></div>
    <div class="metric"><div class="v">{m['done']}</div><div class="l">已完成</div></div>
    <div class="metric"><div class="v">{m['passed']}/{m['checks']}</div><div class="l">验证通过率 {m['rate']}%</div></div>
    <div class="metric"><div class="v">{m['missing']}</div><div class="l">待验证</div></div>
    <div class="metric"><div class="v">{m['verdicts']}</div><div class="l">judge 裁决项</div></div>
  </div>
  <div class="progress">
    <div class="top"><span>整体进度</span><span>{m['done']}/{m['total']} · {m['progress']}%</span></div>
    <div class="bar"><div class="fill" style="width:{m['progress']}%"></div></div>
    {next_html}
  </div>
  <div class="section">
    <h2>📋 Slices（点击展开 obligation）</h2>
    {slice_html}
  </div>
  <div class="section"><h2>📜 变更时间线</h2><div class="tl">{tl_html}</div></div>
  {review_sec}
  <div class="foot">seed-kit living PRD · 机械渲染自 seed status --json + prd.md · derived（可删可重生）</div>
</div>"""


def _load_config(root: Path) -> dict:
    """读 .arbor/config.json（living_prd.enabled 等）；缺失/损坏返回空（用默认）。"""
    p = root / ".arbor" / "config.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> int:
    root = _project_root()
    if not (root / ".arbor" / "tasks").is_dir():
        return 0
    if not _load_config(root).get("living_prd", {}).get("enabled", True):
        return 0  # 用户在 .arbor/config.json 禁用
    found = _find_task(root)
    if not found:
        print("[living_prd] 未找到 prd.md", file=sys.stderr)
        return 0
    task, prd = found
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1]))
    status = _run_seed_status(root, task, plugin_root)
    if not status:
        print(f"[living_prd] seed status --json 失败（task={task}）", file=sys.stderr)
        return 0
    title = _prd_title(prd)
    review_path = prd.parent / "review.md"
    review = review_path.read_text(encoding="utf-8") if review_path.exists() else ""
    git_log = _git_log(root, prd)
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            cwd=str(root), capture_output=True, text=True).stdout.strip() or "—"
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_doc = render(task, title, status, review, git_log, branch, generated)
    out = root / ".arbor" / "artifacts" / "living-prd.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")
    print(f"[living_prd] 已生成 {out.relative_to(root)}（{len(status.get('slices', []))} slices）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
