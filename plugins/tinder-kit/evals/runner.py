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
import json
import os
import pty
import re
import select
import shutil
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

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_ansi(text: str) -> str:
    """去除终端 ANSI 颜色与控制字符。"""
    return ANSI_ESCAPE_RE.sub("", text)


def resolve_provider_config(alias: str) -> tuple[Path, dict[str, str]]:
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
    return settings_file, env_vars


def prepare_sandbox(run_dir: Path, name: str) -> tuple[Path, Path]:
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
    (claude_settings_dir / "settings.json").write_text(
        json.dumps({
            "permissions": {
                "defaultMode": "bypassPermissions",
                "deny": ["AskUserQuestion"],
            },
            "skipDangerousModePermissionPrompt": True,
            "theme": "dark",
        }, indent=2) + "\n",
        encoding="utf-8",
    )

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
    scenario_dir: Path,
    settings_file: Path,
    env_vars: dict[str, str],
    plugin_dir: Path | None,
    max_turns: int = 6,
) -> tuple[str, list[dict[str, str]]]:
    """运行单组（对照组或实验组）的全流程生命周期。"""
    print(f"\n{'='*20} 启动运行组: [{arm_name}] {'='*20}")
    workdir, home_dir = prepare_sandbox(run_dir, arm_name)
    ground_truth_path = scenario_dir / "ground_truth.md"

    supervisor = Supervisor(ground_truth_path, settings_file, home_dir, env_vars)
    driver = PTYDriver(workdir, home_dir, env_vars, plugin_dir)

    driver.start()
    print(f"[{arm_name}] 沙盒初始化完成，工作区: {workdir}")
    print(f"[{arm_name}] 隔离 HOME: {home_dir} (用户个人配置绝对安全)")

    # 1. 等待就绪并下发第一道初始指令
    driver.wait_startup(timeout_sec=25.0)

    if plugin_dir:
        initial_cmd = '/tinder-kit:develop todo "用 Python 开发一个本地 CLI Todo 工具，支持标签过滤与本地持久化"'
    else:
        initial_cmd = '请用 Python 开发一个本地 CLI Todo 工具，支持标签过滤与本地单个 JSON 文件持久化，不要使用数据库'

    print(f"[{arm_name}] 发送初始需求: {initial_cmd}")
    driver.send_input(initial_cmd)

    # 2. 对话与监控循环
    for turn in range(1, max_turns + 1):
        print(f"\n--- [{arm_name}] 进入交互轮次 {turn}/{max_turns} ---")
        output, is_dead = driver.read_until_idle(timeout_sec=180.0)

        if not output.strip() and is_dead:
            print(f"[{arm_name}] 终端进程已退出。")
            break

        print(f"[{arm_name}] 捕获到终端最新输出 ({len(output)} 字符)")

        # 调起 AI 督导官执行监控与作答
        decision = supervisor.react(output[-3000:])
        obs = decision["observation"]
        reply = decision["reply"]
        is_done = decision["is_completed"]

        print(f"  🔍 【AI督导观察】: {obs}")
        print(f"  💬 【产品方答复】: {reply}")

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
    report = supervisor.evaluate_delivery(workdir, title=f"Todo CLI ({arm_name})")
    return report, supervisor.observations


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Tinder-kit 双角色 A/B 评估驱动器")
    parser.add_argument("--provider", default="zhipu-glm", help="渠道别名 (ccz, ccm, ccd 等)")
    parser.add_argument("--scenario", default="todo-cli", help="场景名称 (默认 todo-cli)")
    parser.add_argument("--mode", choices=["treatment", "control", "ab"], default="treatment", help="评估模式")
    parser.add_argument("--max-turns", type=int, default=30, help="最大交互轮次 (默认 30)")
    parser.add_argument("--keep-sandbox", action="store_true", help="保留沙盒目录不自动删除")
    args = parser.parse_args()

    # 1. 解析渠道与凭证
    settings_file, env_vars = resolve_provider_config(args.provider)
    print(f"✓ 成功加载模型凭证配置: {settings_file.name}")

    # 2. 准备运行目录（移至 /tmp 隔离区，彻底断开与本仓库 Git 根目录的关联）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{timestamp}_{uuid.uuid4().hex[:6]}"
    run_dir = Path("/tmp/tinder_evals/sandboxes") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    scenario_dir = EVALS_DIR / "scenarios" / args.scenario
    if not scenario_dir.is_dir():
        print(f"错误: 场景目录不存在: {scenario_dir}")
        return 1

    reports_dir = EVALS_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        final_report_content = f"# 自动化双角色评测大盘 — {args.scenario}\n\n- 时间: {datetime.now().isoformat()}\n- 渠道配置: {args.provider}\n- 模式: {args.mode}\n\n"

        if args.mode in ["treatment", "ab"]:
            t_report, _ = run_single_arm(
                arm_name="treatment_tinder_kit",
                run_dir=run_dir,
                scenario_dir=scenario_dir,
                settings_file=settings_file,
                env_vars=env_vars,
                plugin_dir=PLUGIN_ROOT,
                max_turns=args.max_turns,
            )
            final_report_content += f"## 实验组 (tinder-kit) 评测报告\n\n{t_report}\n\n"

        if args.mode in ["control", "ab"]:
            c_report, _ = run_single_arm(
                arm_name="control_raw_claude",
                run_dir=run_dir,
                scenario_dir=scenario_dir,
                settings_file=settings_file,
                env_vars=env_vars,
                plugin_dir=None,
                max_turns=args.max_turns,
            )
            final_report_content += f"## 对照组 (Raw Claude) 评测报告\n\n{c_report}\n\n"

        report_file = reports_dir / f"{timestamp}_{args.scenario}_{args.mode}.md"
        report_file.write_text(final_report_content, encoding="utf-8")

        print(f"\n{'='*20} 评测全部完成 {'='*20}")
        print(f"✓ 完整 Markdown 评测大盘已归档至: {report_file}")
        print(f"\n{final_report_content}")

        # 自动归档最终产物到 evals/artifacts/ 目录，方便开发者直接检视与运行
        artifacts_dir = EVALS_DIR / "artifacts" / args.scenario
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        for arm in ["treatment_tinder_kit", "control_raw_claude"]:
            src_arm = run_dir / arm
            if src_arm.is_dir():
                dest = artifacts_dir / arm
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(src_arm, dest)
                print(f"✓ 产物已自动持久化归档至: {dest}")

    finally:
        # 清理沙盒
        if not args.keep_sandbox:
            print("\n正在清理临时沙盒...")
            shutil.rmtree(run_dir, ignore_errors=True)
            print("✓ 隔离沙盒临时目录已清理完成。")
        else:
            print(f"\n[--keep-sandbox 生效] 原始沙盒目录已保留于: {run_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
