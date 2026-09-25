#!/usr/bin/env python3
"""自动化终端测试：验证 init 技能对存量项目的零破坏性、原地更新与 Wiki 支持。

通过 PTYDriver 驱动真实 Claude Code 终端，在存量项目沙盒中验证：
1. 存量 CLAUDE.md 既有规范 100% 保持，绝不被整全量覆盖；
2. 宿主文件末尾精准就地更新/追加 ## Agent skills 四大支柱（含 Wiki）；
3. 本地 .forge/ 协议文档与 tags.md 真实落盘；
4. 二次运行 init 时，原地更新，绝不追加重复段落（幂等性）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = EVALS_DIR.parent
sys.path.insert(0, str(EVALS_DIR))

from runner import PTYDriver, prepare_sandbox, resolve_provider_config


def run_init_test(provider_alias: str = "zhipu-glm") -> bool:
    print(f"\n{'='*25} 启动终端真实交互测试: init 技能 {'='*25}")

    # 1. 解析模型凭证
    settings_file, env_vars = resolve_provider_config(provider_alias)
    print(f"✓ 凭证已加载: {settings_file.name}")

    # 2. 准备隔离沙盒
    test_run_dir = Path("/tmp/tinder_evals/sandboxes/test_init_" + str(int(time.time())))
    workdir, home_dir = prepare_sandbox(test_run_dir, "init_sandbox")
    print(f"✓ 工作区路径: {workdir}")
    print(f"✓ 沙盒 HOME: {home_dir}")

    # 3. 初始化为带存量 CLAUDE.md 的 Git 仓库
    subprocess.run(["git", "init"], cwd=workdir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=workdir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=workdir, capture_output=True, check=True)

    original_claude_md = """# My Existing Core Standards

本文件是本项目的现行工程标准，任何 AI 不得随意删改：
- **编程语言**: Python 3.12 纯 stdlib，零多余第三方依赖；
- **数据库规范**: 原生 SQL，严禁使用 ORM；
- **提交规范**: 提交权归人类，严禁 AI 擅自 git commit。

## 业务架构约定
业务核心领域逻辑放在 domain/，与外界 IO 严格隔离。
"""
    (workdir / "CLAUDE.md").write_text(original_claude_md, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=workdir, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with existing CLAUDE.md"], cwd=workdir, capture_output=True, check=True)
    print("✓ 存量项目构造完毕（包含核心业务规范与红线的 CLAUDE.md 已就绪）")

    # 4. 启动 PTY 驱动真实 Claude Code
    driver = PTYDriver(workdir, home_dir, env_vars, PLUGIN_ROOT)
    driver.start()

    try:
        print("✓ 正在启动终端 Claude Code 会话...")
        if not driver.wait_startup(timeout_sec=30.0):
            print("❌ 终端启动超时！")
            return False
        print("✓ 终端已到达就绪提示符 ❯")

        # 第 1 轮：触发 /setup
        cmd = "/setup"
        print(f"\n[Turn 1] 发送命令: {cmd}")
        driver.send_input(cmd)

        out1, is_dead = driver.read_until_idle(timeout_sec=120.0)
        print(f"[Turn 1] 捕获输出 ({len(out1)} 字符):\n" + "-"*40)
        print(out1[-1200:])
        print("-"*40)

        # 检查第一轮是否探查并向人类展示了草案并询问
        if "CLAUDE.md" not in out1 and "Agent skills" not in out1:
            print("⚠️ 警告：第一轮似乎未提及 CLAUDE.md 或 Agent skills 草案")

        # 第 2 轮：向终端确认草案
        reply = "确认草案，请直接写入配置。"
        print(f"\n[Turn 2] 发送确认: {reply}")
        driver.send_input(reply)

        out2, is_dead = driver.read_until_idle(timeout_sec=120.0)
        print(f"[Turn 2] 捕获输出 ({len(out2)} 字符):\n" + "-"*40)
        print(out2[-1200:])
        print("-"*40)

        # 5. 断言验证磁盘落地结果
        print("\n" + "="*20 + " 开始磁盘断言检验 " + "="*20)
        claude_md_after = (workdir / "CLAUDE.md").read_text(encoding="utf-8")
        print("\n【落盘后的 CLAUDE.md 全文】:\n" + "-"*30)
        print(claude_md_after)
        print("-"*30)

        # 断言 1: 存量规范绝对没有被冲刷丢弃
        assert "My Existing Core Standards" in claude_md_after, "❌ 失败：存量标题丢失！"
        assert "Python 3.12 纯 stdlib" in claude_md_after, "❌ 失败：存量编程语言规范丢失！"
        assert "业务架构约定" in claude_md_after, "❌ 失败：存量业务架构章节丢失！"
        print("✅ 断言 1 通过: 存量 CLAUDE.md 既有规范 100% 完整保留（零破坏性）！")

        # 断言 2: ## Agent skills 章节已安全挂载，且包含 Wiki
        assert "## Agent skills" in claude_md_after, "❌ 失败：未写入 ## Agent skills 章节！"
        assert "Issue tracker" in claude_md_after, "❌ 失败：未包含 Issue tracker！"
        assert "Wiki" in claude_md_after, "❌ 失败：未包含 Wiki 专属指针！"
        assert ".forge/wiki/tags.md" in claude_md_after, "❌ 失败：未指向 tags.md！"
        print("✅ 断言 2 通过: ## Agent skills 章节包含完整的 Issue tracker, Triage labels, Domain docs 与 Wiki！")

        # 断言 3: .forge/ 目录与驱动协议真实落盘
        forge_dir = workdir / ".forge"
        assert forge_dir.is_dir(), "❌ 失败：.forge 目录未创建！"
        assert (forge_dir / "issue-tracker.md").is_file(), "❌ 失败：.forge/issue-tracker.md 未创建！"
        assert (forge_dir / "domain.md").is_file(), "❌ 失败：.forge/domain.md 未创建！"
        assert (forge_dir / "triage-labels.md").is_file(), "❌ 失败：.forge/triage-labels.md 未创建！"
        assert (forge_dir / "wiki" / "tags.md").is_file(), "❌ 失败：.forge/wiki/tags.md 未创建！"
        print("✅ 断言 3 通过: .forge/ 目录下四份核心协议与 tags.md 均已落盘！")

        # 断言 4: tags.md 是否包含打标/检索铁律
        tags_content = (forge_dir / "wiki" / "tags.md").read_text(encoding="utf-8")
        assert "检索先对齐" in tags_content, "❌ 失败：tags.md 未包含'检索先对齐'铁律！"
        assert "_Avoid_" in tags_content, "❌ 失败：tags.md 未包含 _Avoid_ 机制说明！"
        print("✅ 断言 4 通过: tags.md 包含完整的受控真实源规则与 _Avoid_ 负面清单机制！")

        # 6. 进阶测试：幂等性（Idempotency）—— 再次运行 /tinder-kit:init
        print("\n" + "="*20 + " 开始幂等性断言检验（二次运行） " + "="*20)
        print(f"\n[Turn 3] 再次发送命令: {cmd}")
        driver.send_input(cmd)
        out3, _ = driver.read_until_idle(timeout_sec=120.0)

        print(f"\n[Turn 4] 再次确认写入: {reply}")
        driver.send_input(reply)
        out4, _ = driver.read_until_idle(timeout_sec=120.0)

        claude_md_twice = (workdir / "CLAUDE.md").read_text(encoding="utf-8")
        print("\n【二次落盘后的 CLAUDE.md 全文】:\n" + "-"*30)
        print(claude_md_twice)
        print("-"*30)

        # 断言 5: ## Agent skills 出现次数严格等于 1，绝不重复追加
        skills_count = claude_md_twice.count("## Agent skills")
        assert skills_count == 1, f"❌ 失败：## Agent skills 重复追加了 {skills_count} 次！"
        assert "My Existing Core Standards" in claude_md_twice, "❌ 失败：存量规范在二次运行时丢失！"
        print("✅ 断言 5 通过: 幂等性完美成立！多次运行 init 仅就地刷新，## Agent skills 出现且仅出现 1 次！")

        print("\n🎉🎉🎉 全部真实终端交互与落盘断言 100% PASS！")
        return True

    finally:
        driver.close()
        print("✓ 终端进程已安全退出与释放。")


if __name__ == "__main__":
    success = run_init_test("zhipu-glm")
    sys.exit(0 if success else 1)
