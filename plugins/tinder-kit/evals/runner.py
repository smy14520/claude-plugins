#!/usr/bin/env python3
"""Tinder-Kit 自动化双角色评估驱动器 (Eval Runner)

特性：
1. 绝对沙盒隔离：独立 HOME 目录，用户真实 ~/.claude/ 配置 100% 零修改、零污染。
2. 原生多渠道支持：无缝支持 ccz (zhipu)、ccm (minimax)、ccd (deepseek) 等配置。
3. 双角色对决：AI 督导官（Supervisor）负责监控、答疑与验收；真实 Claude Code 终端执行。
4. A/B 基线对比：支持单跑实验组、对照组，或一键 A/B 对照评测。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# 将 evals 加入路径
EVALS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = EVALS_DIR.parent
sys.path.insert(0, str(EVALS_DIR))

from supervisor import Supervisor
from scenario_loader import Scenario, load_scenario, list_available_scenarios

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_ansi(text: str) -> str:
    """去除终端 ANSI 颜色与控制字符。"""
    return ANSI_ESCAPE_RE.sub("", text)


def resolve_provider_config(alias: str, model_override: str | None = None) -> tuple[Path, dict[str, str]]:
    """解析渠道别名并加载配置（对齐 ~/Personal/Config/claudeConfig 体系）。"""
    alias_map = {
        "ccz": "zhipu-glm",
        "zhipu": "zhipu-glm",
        "zhipu-glm": "zhipu-glm",
        "ccm": "minimax",
        "minimax": "minimax",
        "ccd": "deepseek",
        "deepseek": "deepseek",
        "cca": "ali-qwen",
        "ccc": "anthropic",
        "ccg": "grok",
    }
    provider = alias_map.get(alias.lower(), alias)
    config_dir = Path.home() / "Personal/Config/claudeConfig"
    settings_file = config_dir / f"settings-{provider}.json"

    if not settings_file.is_file():
        # 如果 settings 还没生成，尝试跑 switch.sh
        switch_sh = config_dir / "switch.sh"
        if switch_sh.is_file():
            import subprocess
            subprocess.run([str(switch_sh), provider], check=False)

    if not settings_file.is_file():
        raise FileNotFoundError(f"未找到提供商配置文件: {settings_file}")

    with open(settings_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    env_vars = data.get("env", {})

    if model_override:
        for k in [
            "ANTHROPIC_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "CLAUDE_CODE_SUBAGENT_MODEL",
        ]:
            env_vars[k] = model_override
        data["env"] = env_vars
        temp_settings = Path(f"/tmp/settings-{provider}-{model_override.replace('/', '_')}.json")
        temp_settings.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        settings_file = temp_settings

    return settings_file, env_vars


def prepare_sandbox(run_dir: Path, name: str, env_vars: dict[str, str] | None = None) -> tuple[Path, Path]:
    """创建隔离的工作区与沙盒 HOME，保证主配置零污染。"""
    workdir = run_dir / name
    home_dir = run_dir / f"{name}_home"

    workdir.mkdir(parents=True, exist_ok=True)
    home_dir.mkdir(parents=True, exist_ok=True)

    # 规范化绝对路径（处理 macOS /tmp -> /private/tmp）
    canonical_workdir = os.path.realpath(workdir)
    canonical_home = os.path.realpath(home_dir)

    # 全面预埋路径变体，100% 豁免信任对话框和引导
    projects_config = {}
    for p in [str(workdir), canonical_workdir]:
        projects_config[p] = {
            "hasTrustDialogAccepted": True,
            "hasCompletedProjectOnboarding": True,
        }
        if p.startswith("/private"):
            projects_config[p[8:]] = {
                "hasTrustDialogAccepted": True,
                "hasCompletedProjectOnboarding": True,
            }
        else:
            projects_config[f"/private{p}"] = {
                "hasTrustDialogAccepted": True,
                "hasCompletedProjectOnboarding": True,
            }

    # 初始化全新的 .claude.json，跳过 Onboarding 引导和信任对话框
    claude_json = Path(canonical_home) / ".claude.json"
    claude_json.write_text(
        json.dumps({
            "numStartups": 10,
            "hasCompletedOnboarding": True,
            "lastOnboardingVersion": "2.1.228",
            "migrationVersion": 13,
            "theme": "dark",
            "projects": projects_config,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    # 写入权限与安全设置（禁用 AskUserQuestion 弹窗交互，促使模型直接在对话流中提出高质量访谈问题）
    claude_settings_dir = Path(canonical_home) / ".claude"
    claude_settings_dir.mkdir(parents=True, exist_ok=True)
    settings_payload: dict = {
        "permissions": {
            "defaultMode": "bypassPermissions",
            "deny": ["AskUserQuestion"],
        },
        "skipDangerousModePermissionPrompt": True,
        "theme": "dark",
    }
    if env_vars:
        settings_payload["env"] = env_vars

    (claude_settings_dir / "settings.json").write_text(
        json.dumps(settings_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return Path(canonical_workdir), Path(canonical_home)

    return Path(canonical_workdir), Path(canonical_home)


class PTYDriver:
    """基于伪终端 (PTY) 驱动 Claude Code，支持双向交互。"""

    def __init__(self, workdir: Path, home_dir: Path, env_vars: dict[str, str], plugin_dir: Path | None = None):
        self.workdir = workdir
        self.home_dir = home_dir
        self.env_vars = env_vars
        self.plugin_dir = plugin_dir
        self.master: int | None = None
        self.pid: int | None = None
        self.last_saw_busy = False

    def start(self) -> None:
        master, slave = pty.openpty()
        self.master = master

        env = os.environ.copy()
        # 彻底清洗掉父级 Claude 会话注入的内部环境变量，防止子进程被识别为 child session
        for k in list(env.keys()):
            if k.startswith("CLAUDE_") and k not in [
                "CLAUDE_CODE_HARBOR_KITE",
                "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE",
                "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
                "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
                "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
            ]:
                env.pop(k, None)
        env.pop("CLAUDECODE", None)
        env.pop("AI_AGENT", None)

        env["HOME"] = str(self.home_dir)
        env.update(self.env_vars)

        if self.plugin_dir:
            bin_dir = self.plugin_dir / "bin"
            if bin_dir.is_dir():
                env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        cmd = ["claude", "--dangerously-skip-permissions"]
        if self.plugin_dir:
            cmd.extend(["--plugin-dir", str(self.plugin_dir)])

        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.setsid()
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            os.chdir(self.workdir)
            os.execvpe("claude", cmd, env)
        else:
            os.close(slave)
            self.pid = pid

    def _write_chunked(self, data: bytes, chunk_size: int = 16, delay: float = 0.005) -> None:
        """分块节流写入 PTY，彻底防止 macOS/Linux 终端行规程与 Node TUI 按键队列溢出丢字。"""
        for i in range(0, len(data), chunk_size):
            os.write(self.master, data[i : i + chunk_size])
            time.sleep(delay)

    def send_input(self, text: str) -> None:
        """往终端发送文本与回车。对于斜杠命令，先发命令名展开，再发参数；对于普通文本，采用分块节流写入，保证字符 100% 零丢失。"""
        if self.master is None:
            return
        clean_text = text.strip()

        # 容错兜底：若答复中包含开工指令 /implement 但被 LLM 督导官前置了客套话，自动提取纯净指令以保证触发 Slash Command
        if "/implement" in clean_text and not clean_text.startswith("/"):
            clean_text = "/implement"

        if clean_text.startswith("/"):
            parts = clean_text.split(" ", 1)
            cmd_name = parts[0]
            self._write_chunked((cmd_name + " ").encode("utf-8"))
            time.sleep(0.4)
            if len(parts) > 1:
                self._write_chunked(parts[1].encode("utf-8"))
                time.sleep(0.3)
                os.write(self.master, b"\r")
            else:
                os.write(self.master, b"\r")
        else:
            self._write_chunked(clean_text.encode("utf-8"), chunk_size=16, delay=0.005)
            time.sleep(0.3)
            os.write(self.master, b"\r")

    def wait_startup(self, timeout_sec: float = 25.0) -> bool:
        """等待终端初始化并到达首个提示符就绪状态。"""
        if self.master is None:
            return False
        buf = b""
        start = time.time()
        while time.time() - start < timeout_sec:
            r, _, _ = select.select([self.master], [], [], 0.2)
            if r:
                try:
                    chunk = os.read(self.master, 4096)
                    buf += chunk
                    if b"]0;\xe2\x9c\xb3 Claude Code" in chunk:
                        time.sleep(1.0)
                        # 彻底排空启动过程中的所有剩余字符
                        while True:
                            r2, _, _ = select.select([self.master], [], [], 0.1)
                            if not r2:
                                break
                            os.read(self.master, 4096)
                        return True
                except OSError:
                    return False
        return False

    def read_until_idle(self, timeout_sec: float = 240.0) -> tuple[str, bool]:
        """读取终端输出，严格等待两阶段状态翻转：
        1. 必须先观察到 busy 状态（产生输出，包含 interrupt 或 spinner 旋转光标）；
        2. 随后等待 idle 状态（标题变回 ✳ Claude Code，且末尾为输入提示符 ❯）。
        """
        if self.master is None:
            return "", False

        full_chunks: list[bytes] = []
        start_time = time.time()
        last_rec = time.time()
        saw_busy = False
        self.last_saw_busy = False
        sent_safeguard_enter = False

        while time.time() - start_time < timeout_sec:
            # 兜底：若 3 秒内未观察到 busy 翻转，补发一次回车以防输入未被终端捕获
            if (not saw_busy) and (not sent_safeguard_enter) and (time.time() - start_time >= 3.0):
                try:
                    os.write(self.master, b"\r")
                except OSError:
                    pass
                sent_safeguard_enter = True

            r, _, _ = select.select([self.master], [], [], 0.3)
            if r:
                try:
                    chunk = os.read(self.master, 4096)
                    if not chunk:
                        all_text = b"".join(full_chunks)
                        return clean_ansi(all_text.decode("utf-8", errors="replace")), True
                    full_chunks.append(chunk)
                    last_rec = time.time()

                    # 检查是否进入 busy 状态（包含 interrupt 或 spinner 字符或思考标签）
                    clean_chunk = clean_ansi(chunk.decode("utf-8", errors="ignore")).lower()
                    if (
                        "interrupt" in clean_chunk
                        or any(s in chunk for s in [b"\xe2\x97\x90", b"\xe2\x97\x91", b"\xe2\x97\x92", b"\xe2\x97\x93"])
                        or any(w in clean_chunk for w in ["thinking", "thought for", "reading", "running"])
                    ):
                        saw_busy = True
                        self.last_saw_busy = True

                    # 兜底：若意外遇到单选/多选交互组件，自动发送回车确认推荐项
                    if "enter to select" in clean_chunk or "entertoselect" in clean_chunk:
                        time.sleep(0.3)
                        os.write(self.master, b"\r")

                    # 若已观察到 busy，且检测到 idle 状态（标题包含 ✳ 且 interrupt 已消失）
                    if saw_busy and (b"]0;\xe2\x9c\xb3" in chunk) and ("interrupt" not in clean_chunk):
                        time.sleep(0.3)
                        while True:
                            r2, _, _ = select.select([self.master], [], [], 0.1)
                            if not r2:
                                break
                            try:
                                extra = os.read(self.master, 4096)
                                if not extra:
                                    break
                                full_chunks.append(extra)
                            except OSError:
                                break
                        all_text = b"".join(full_chunks)
                        return clean_ansi(all_text.decode("utf-8", errors="replace")), False
                except OSError:
                    all_text = b"".join(full_chunks)
                    return clean_ansi(all_text.decode("utf-8", errors="replace")), True
            else:
                # 若已 busy 且出现静默窗口（例如超过 5 秒无新输出），检查是否提示符已到位且 interrupt 消失
                if saw_busy and (time.time() - last_rec >= 5.0):
                    all_text = b"".join(full_chunks)
                    clean_all = clean_ansi(all_text.decode("utf-8", errors="replace"))
                    tail = clean_all[-300:].lower()
                    if "interrupt" not in tail and ("❯" in clean_all[-100:] or "?" in tail):
                        return clean_all, False
                # 防挂起兜底：若等待超 15 秒从未触发 busy，且已就绪
                elif (not saw_busy) and (time.time() - start_time >= 15.0) and (time.time() - last_rec >= 3.0):
                    all_text = b"".join(full_chunks)
                    clean_all = clean_ansi(all_text.decode("utf-8", errors="replace"))
                    if "❯" in clean_all[-100:] or b"]0;\xe2\x9c\xb3" in all_text:
                        return clean_all, False

        all_text = b"".join(full_chunks)
        return clean_ansi(all_text.decode("utf-8", errors="replace")), False

    def close(self) -> None:
        if self.pid:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
            except Exception:
                pass
        if self.master:
            try:
                os.close(self.master)
            except Exception:
                pass


def run_single_arm(
    arm_name: str,
    run_dir: Path,
    scenario: Scenario,
    settings_file: Path,
    env_vars: dict[str, str],
    plugin_dir: Path | None,
    max_turns: int = 30,
) -> tuple[str, list[dict[str, str]], dict]:
    """运行单组（对照组或实验组）的全流程生命周期。"""
    print(f"\n{'='*20} 启动运行组: [{arm_name}] {'='*20}")
    workdir, home_dir = prepare_sandbox(run_dir, arm_name, env_vars)

    # 支持 seed_files 初始代码预埋（如小需求/存量项目/故障靶场）
    seed_dir = scenario.scenario_dir / "seed_files"
    if seed_dir.is_dir():
        for item in seed_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, workdir / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, workdir / item.name)

    # 初始化 git 仓库（若未初始化）
    if not (workdir / ".git").is_dir():
        subprocess.run(["git", "init"], cwd=workdir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", f"{arm_name} Tester"], cwd=workdir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=workdir, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=workdir, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=workdir, capture_output=True, check=True)

    if arm_name == "mattpocock_skills":
        # 拷贝 Matt Pocock 的原生 skills 至沙盒项目 .claude/skills/
        mp_skills_src = Path("/Users/camellia/Personal/Code/claude/mattpocock-skills/skills")
        target_skills = workdir / ".claude" / "skills"
        target_skills.mkdir(parents=True, exist_ok=True)
        for category in ["engineering", "productivity"]:
            cat_dir = mp_skills_src / category
            if cat_dir.is_dir():
                for skill_dir in cat_dir.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                        shutil.copytree(skill_dir, target_skills / skill_dir.name, dirs_exist_ok=True)

        # 预埋 Matt Pocock 技能依赖的 issue-tracker 与 domain 规则文档
        docs_agents = workdir / "docs" / "agents"
        docs_agents.mkdir(parents=True, exist_ok=True)
        (docs_agents / "issue-tracker.md").write_text("# Issue tracker: Local Markdown\nIssues and specs live in .scratch/\n", encoding="utf-8")
        (docs_agents / "domain.md").write_text("# Domain Docs\nRead CONTEXT.md and docs/adr/ if present.\n", encoding="utf-8")

    initial_cmd = scenario.get_initial_cmd(arm_name)
    supervisor = Supervisor(
        ground_truth_path=scenario.ground_truth,
        settings_file=settings_file,
        sandbox_home=home_dir,
        env_vars=env_vars,
        supervisor_taste=scenario.supervisor_taste,
    )
    driver = PTYDriver(workdir, home_dir, env_vars, plugin_dir)

    driver.start()
    print(f"[{arm_name}] 沙盒初始化完成，工作区: {workdir}")
    print(f"[{arm_name}] 隔离 HOME: {home_dir} (用户个人配置绝对安全)")

    # 1. 等待就绪并下发第一道初始指令
    driver.wait_startup(timeout_sec=30.0)

    # 若为 tinder-kit 且场景允许 setup，执行 /setup 脚手架化项目驱动、CLAUDE.md 与受控标签词典
    if plugin_dir and scenario.setup_project:
        print(f"\n[{arm_name}] Step 0: 先通过 /setup 初始化本地 Markdown 驱动、CLAUDE.md 指针与 Wiki tags")
        driver.send_input("/setup")
        out_setup, _ = driver.read_until_idle(timeout_sec=120.0)
        print(f"[{arm_name}] 收到 setup 汇报草案，发送确认写入")
        driver.send_input("确认草案，请直接写入配置。")
        out_confirm, _ = driver.read_until_idle(timeout_sec=120.0)
        print(f"[{arm_name}] ✓ /setup 完成，.forge/ 核心驱动与 Wiki tags 真实落盘")

    print(f"\n[{arm_name}] 发送初始需求: {initial_cmd}")
    driver.send_input(initial_cmd)

    effective_max_turns = min(max_turns, scenario.max_turns)
    # 2. 对话与监控循环
    for turn in range(1, effective_max_turns + 1):
        print(f"\n--- [{arm_name}] 进入交互轮次 {turn}/{effective_max_turns} ---")
        output, is_dead = driver.read_until_idle(timeout_sec=180.0)

        if not output.strip() and is_dead:
            print(f"[{arm_name}] 终端进程已退出。")
            break

        # 模型根本没开始工作：上一条输入还停在输入框里（回车未提交）。
        # 此时督导官看到的只是输入框回显，若照常作答，答复会被拼进同一条未提交的消息。
        # 补发回车等它真正提交，最多重试 3 次，不消耗督导官的作答。
        retries = 0
        while not driver.last_saw_busy and not is_dead and retries < 3:
            retries += 1
            print(f"[{arm_name}] 未观察到模型开始工作，补发回车提交输入（第 {retries} 次）")
            os.write(driver.master, b"\r")
            more, is_dead = driver.read_until_idle(timeout_sec=180.0)
            output += more

        print(f"[{arm_name}] 捕获到终端最新输出 ({len(output)} 字符)")

        # 调起 AI 督导官执行监控与作答
        decision = supervisor.react(output[-3000:])
        obs = decision["observation"]
        reply = decision["reply"]
        is_done = decision["is_completed"]

        print(f"  🔍 【AI督导观察 [{arm_name}]】: {obs}")
        print(f"  💬 【产品方答复 [{arm_name}]】: {reply}")

        if is_done:
            print(f"[{arm_name}] 督导官判定任务已彻底交付完工！🎉")
            break

        # 往终端输入答复
        driver.send_input(reply)
        time.sleep(1.0)

    # 善后关闭
    driver.close()

    # 3. 督导官撰写最终质量评测报告
    print(f"\n[{arm_name}] 正在由 AI 督导官审查产物并撰写评测报告...")
    report = supervisor.evaluate_delivery(workdir, title=f"{scenario.slug} ({arm_name})")
    return report, supervisor.observations, supervisor.last_delivery_data


KNOWN_ARMS = {
    "develop": ("tinder_develop", PLUGIN_ROOT, "Tinder-kit develop 自动编排流 (tinder_develop)"),
    "tinder_develop": ("tinder_develop", PLUGIN_ROOT, "Tinder-kit develop 自动编排流 (tinder_develop)"),
    "treatment": ("tinder_develop", PLUGIN_ROOT, "Tinder-kit develop 自动编排流 (tinder_develop)"),
    "manual": ("tinder_manual", PLUGIN_ROOT, "Tinder-kit 手动分步流 (tinder_manual)"),
    "tinder_manual": ("tinder_manual", PLUGIN_ROOT, "Tinder-kit 手动分步流 (tinder_manual)"),
    "mattpocock": ("mattpocock_skills", None, "Matt Pocock 原生套件 (mattpocock-skills)"),
    "mattpocock_skills": ("mattpocock_skills", None, "Matt Pocock 原生套件 (mattpocock-skills)"),
    "control": ("control_raw_claude", None, "对照组 (Raw Claude)"),
    "raw": ("control_raw_claude", None, "对照组 (Raw Claude)"),
    "control_raw_claude": ("control_raw_claude", None, "对照组 (Raw Claude)"),
}

MODE_ARMS = {
    "triple": ["mattpocock_skills", "tinder_manual", "tinder_develop"],
    "tinder_both": ["tinder_manual", "tinder_develop"],
    "ab": ["control_raw_claude", "tinder_develop"],
    "treatment": ["tinder_develop"],
    "manual": ["tinder_manual"],
    "mattpocock": ["mattpocock_skills"],
    "control": ["control_raw_claude"],
}


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Tinder-kit 声明式 E2E 与单技能评测驱动器")
    parser.add_argument("--list-scenarios", action="store_true", help="列出所有可用场景并退出")
    parser.add_argument("--provider", default="zhipu-glm", help="渠道别名 (ccz, ccm, ccd 等)")
    parser.add_argument("--model", default="glm-5.3-flashX", help="指定模型名称 (默认 glm-5.3-flashX)")
    parser.add_argument("--scenario", default="todo-cli", help="场景名称、slug 或路径 (例如 small-due, todo-cli, large-wiki 等)")
    parser.add_argument(
        "--mode",
        choices=["triple", "treatment", "control", "ab", "mattpocock", "manual", "tinder_both"],
        default="treatment",
        help="预设评估模式：triple (三路并发对比), tinder_both (develop + manual), treatment, ab 等",
    )
    parser.add_argument(
        "--arms",
        help="【自定义运行组】逗号分隔列表，例如: develop,manual 或 develop,mattpocock。显式指定时覆盖 --mode",
    )
    parser.add_argument("--max-turns", type=int, default=30, help="最大交互轮次 (默认 30)")
    parser.add_argument("--keep-sandbox", action="store_true", help="保留沙盒目录不自动删除")
    args = parser.parse_args()

    scenarios_root = EVALS_DIR / "scenarios"
    if args.list_scenarios:
        scenarios = list_available_scenarios(scenarios_root)
        print("\n" + "=" * 55)
        print("📋 可用评测场景清单 (Available Scenarios):")
        print("=" * 55)
        for s in scenarios:
            desc = f" - {s['description']}" if s['description'] else ""
            print(f"• [{s['slug']}] ({s['type']}){desc}")
        print("=" * 55 + "\n")
        return 0

    # 1. 动态加载场景
    try:
        scenario = load_scenario(args.scenario, scenarios_root)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return 1

    print(f"\n{'='*25} 加载场景: [{scenario.slug}] {'='*25}")
    print(f"名称: {scenario.name}")
    print(f"类型: {scenario.scenario_type}")
    if scenario.description:
        print(f"描述: {scenario.description}")
    print(f"最大轮次: {min(args.max_turns, scenario.max_turns)}")

    # 2. 解析运行组 (arms_to_run)
    if args.arms:
        arm_keys = [k.strip().lower() for k in args.arms.split(",") if k.strip()]
        arms_to_run = []
        for k in arm_keys:
            if k in KNOWN_ARMS:
                val = KNOWN_ARMS[k]
                if val not in arms_to_run:
                    arms_to_run.append(val)
            else:
                print(f"警告: 未知运行组 '{k}'，已跳过。可选组: {list(KNOWN_ARMS.keys())}")
        if not arms_to_run:
            print("错误: 未指定任何合法的运行组！")
            return 1
    else:
        arm_keys = MODE_ARMS.get(args.mode, ["tinder_develop"])
        arms_to_run = [KNOWN_ARMS[k] for k in arm_keys]

    active_arms = [a[0] for a in arms_to_run]
    print(f"激活测试组: {active_arms}\n")

    # 3. 解析渠道与凭证
    settings_file, env_vars = resolve_provider_config(args.provider, model_override=args.model)
    print(f"✓ 成功加载模型凭证配置: {settings_file.name} (模型: {args.model})")

    # 4. 准备沙盒根目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{timestamp}_{uuid.uuid4().hex[:6]}"
    run_dir = Path("/tmp/tinder_evals/sandboxes") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    reports_dir = EVALS_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        final_report_content = (
            f"# 自动化多角色评测大盘 — {scenario.name} ({scenario.slug})\n\n"
            f"- 场景类型: {scenario.scenario_type}\n"
            f"- 时间: {datetime.now().isoformat()}\n"
            f"- 渠道配置: {args.provider}\n"
            f"- 评估模型: {args.model}\n"
            f"- 测试组: {', '.join(active_arms)}\n\n"
        )

        reports_dict = {}
        delivery_data_dict = {}

        if len(arms_to_run) > 1:
            print(f"\n{'='*25} 启动并发多路评测 ({len(arms_to_run)} 组并发) {'='*25}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(arms_to_run)) as executor:
                future_map = {
                    executor.submit(
                        run_single_arm,
                        arm_name,
                        run_dir,
                        scenario,
                        settings_file,
                        env_vars,
                        p_dir,
                        args.max_turns,
                    ): (arm_name, label)
                    for arm_name, p_dir, label in arms_to_run
                }

                for future in concurrent.futures.as_completed(future_map):
                    arm_name, label = future_map[future]
                    try:
                        rep, obs, deliv = future.result()
                        reports_dict[arm_name] = rep
                        delivery_data_dict[label] = deliv
                        print(f"\n[{arm_name}] ✓ 评测已顺利完成！")
                    except Exception as e:
                        print(f"\n[{arm_name}] ✗ 评测运行出错: {e}")
                        reports_dict[arm_name] = f"# 评测异常\n错误: {e}"
        else:
            arm_name, p_dir, label = arms_to_run[0]
            rep, obs, deliv = run_single_arm(
                arm_name=arm_name,
                run_dir=run_dir,
                scenario=scenario,
                settings_file=settings_file,
                env_vars=env_vars,
                plugin_dir=p_dir,
                max_turns=args.max_turns,
            )
            reports_dict[arm_name] = rep
            delivery_data_dict[label] = deliv

        # 5. 若多方案并发（>= 2 组），调起横向主观盲测对比评审
        if len(arms_to_run) >= 2 and len(delivery_data_dict) >= 2:
            print(f"\n{'='*25} 启动多方案横向主观盲测对比评审 {'='*25}")
            supervisor_home = run_dir / "supervisor_home"
            supervisor_home.mkdir(parents=True, exist_ok=True)
            critique = Supervisor.compare_arms(
                arms_data=delivery_data_dict,
                ground_truth=scenario.ground_truth,
                supervisor_taste=scenario.supervisor_taste,
                settings_file=settings_file,
                sandbox_home=supervisor_home,
                env_vars=env_vars,
            )
            final_report_content += f"## ⚖️ 多方案横向主观对比裁决大盘 (Side-by-side Critique)\n\n{critique}\n\n---\n\n"

        # 6. 追加各组独立质检报告
        final_report_content += "## 各方案独立质检报告\n\n"
        for arm_name, _, label in arms_to_run:
            final_report_content += f"### {label}\n\n{reports_dict.get(arm_name, '（无报告产出）')}\n\n---\n\n"

        report_file = reports_dir / f"{timestamp}_{scenario.slug}_{args.mode}_{args.model}.md"
        report_file.write_text(final_report_content, encoding="utf-8")

        print(f"\n{'='*20} 评测全部完成 {'='*20}")
        print(f"✓ 完整 Markdown 评测大盘已归档至: {report_file}")

        # 自动归档最终产物到 evals/artifacts/ 目录
        artifacts_dir = EVALS_DIR / "artifacts" / scenario.slug
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        for arm in active_arms:
            src_arm = run_dir / arm
            if src_arm.is_dir():
                dest = artifacts_dir / arm
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(src_arm, dest)
                print(f"✓ 产物已自动持久化归档至: {dest}")

        print(f"\n{final_report_content[:2000]}...\n[更多详情请查阅报告: {report_file}]")

    finally:
        # 清理沙盒
        if not args.keep_sandbox:
            shutil.rmtree(run_dir, ignore_errors=True)
            print(f"✓ 沙盒已安全清理: {run_dir}")
        else:
            print(f"[--keep-sandbox 生效] 原始沙盒目录已保留于: {run_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
