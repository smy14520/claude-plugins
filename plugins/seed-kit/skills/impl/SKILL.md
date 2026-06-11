---
name: impl
description: "执行一个 seed-kit 任务的 PRD：seed status 找到断点，按顺序逐 slice 实现，run-check 落盘证据后 seed done 勾选，提示用户 commit。代码就是进度。"
---
# Impl — 逐 slice 执行 PRD

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

执行 `.seed/tasks/<task>/prd.md`：PRD 是需求 source of truth，impl 写代码不改需求。

## 入场

1. `seed status <task>` —— 这是唯一的断点续作入口：结构错误先停下报告；否则从 `next` 指向的 slice 继续。
2. 通读 prd.md 全文（AC、Technical Framing、全部 Slices、变更记录），理解整体再动手。
3. 只有用户明确指定时才读 research / wiki。

## Slice 循环

对每个未完成 slice，按顺序连续执行（不在 slice 之间停顿等待确认）：

1. 围绕该 slice 的验收实现，按 AC 补测试；不弱化断言、不吞异常、不悄悄收窄 scope。
2. `seed run-check <task> --slice S-NNN -- <PRD 声明的命令>` 逐项执行；失败就修代码再跑，不换命令。
3. `[manual]` 项真实验证后用 `--manual --note --evidence` 记录；不允许把可自动化的检查当 manual 处理。
4. `seed done <task> --slice S-NNN` 勾选；helper 会列出缺口，按缺口补齐。
5. 提示用户 commit 本 slice 的改动（agent 不自动 commit）。

## 卡住协议

显式停下，不硬做、不绕过：

- **需求缺口**（PRD 信息缺失/冲突/与代码现状不符）：在 `## 变更记录` 写明缺口，停下来向用户说明，等待用户补充或转 brainstorm。
- **环境阻塞**（依赖、权限、外部服务）：说明哪条验证无法执行、为什么，等待用户处理；不要把跑不了的命令改记成 manual。

## 结束

所有 slice 完成后：汇总本次改动范围与证据位置，建议用户触发 review。不自动触发。
