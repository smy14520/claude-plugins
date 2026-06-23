---
name: impl
description: "执行一个 seed-kit 任务的 PRD：seed status 找到断点，按顺序逐 slice 实现，run-check 落盘证据后 seed done 勾选，提示用户 commit。代码就是进度。"
---
# Impl — 逐 slice 执行 PRD

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

执行 `.arbor/tasks/<task>/prd.md`：PRD 是需求 source of truth，impl 写代码不改需求。

**地板，不是天花板。** 过验证只是地板；目标是把每个交付面做到**可交付品质**，不是“刚好让 check 变绿就停”。在地板保持绿的前提下，工艺/体验/手感放手做好——不要交付半成品。`seed done` 勾选只代表声明义务已过 gate：若声明了 scoring judge，也代表该义务达到项目 rubric；不代表未声明维度或整体品味没有上限。

## 入场

1. `seed status <task>` —— 这是唯一的断点续作入口：结构错误先停下报告；否则从 `next` 指向的 slice 继续。
2. 通读 prd.md 全文（AC、Technical Framing、Slices 索引、变更记录），理解整体再动手。
3. 只有用户明确指定时才读 research / wiki。

## Slice 循环

对每个未完成 slice，按顺序连续执行（不在 slice 之间停顿等待确认）：

**动手前先声明本 slice 的 USE / BUILD**（写出来，一行）：基座（脚手架/安装器、库、既有代码、helper、事实源）用现成的，核心逻辑自己写——别手搓框架能生成的东西，也别拉个成品冒充交付；拿不准的边界交 review。

1. 读 `slices/S-NNN.md`，围绕其验收与 `## 交付面` 实现，按 AC 补测试；不弱化断言、不吞异常、不悄悄收窄 scope。功能正确之外，把该交付面做到可交付品质——UI 不是半成品、文案不是占位、输出与手感经得起真实使用。
2. 按验证项的**义务（obligation）**逐条落证据；`[kind][surface]` 的 surface 不要改窄或改成别的面：
   - `[assert][...]`：`seed run-check <task> --slice S-NNN --obligation <id> -- <会失败的断言>` 真实执行，绑定到义务；失败就修代码再跑，不弱化断言。命令必须是会失败的断言——裸 curl/echo 这类烟雾命令对非 compliance 面会被 seed 硬阻断，改成真正断言（测试套件、`curl -sf`、管道断言）。
   - `[judge][...]`：**impl 不自裁**（生成者≠验证者）——由 `/seed-kit:review-loop` 的 seed-judge 看真实 artifact、按项目 rubric 裁决，impl 不自己打分。
   - `[human][compliance]`：提示用户/stakeholder 签收，用 `seed run-check ... --obligation <id> --note "<结论>" --by "<签收人>"` 记录。
3. 不允许把可 assert 的交付面降级成 judge/human 充数，也不要用后端断言冒充 web-ui/e2e 覆盖。
4. **assert 绿后跑 `/seed-kit:review-loop`** 审到收敛（审代码+产物+propose-kill 批量证伪，每个 slice 都跑，不只 `[judge]`）；未收敛按 review 返工清单修再 review。收敛后 `seed review-mark <task> --slice S-NNN --verdict converged` 落 marker，再 `seed done <task> --slice S-NNN`——review_gate hook 查 marker，没过 review-loop 不放行勾选（helper 另按 `[kind]` + obligation 列证据缺口，按缺口补齐）。
5. 提示用户 commit 本 slice 的改动（agent 不自动 commit）。

## 卡住协议

显式停下，不硬做、不绕过：

- **需求缺口**（PRD 信息缺失/冲突/与代码现状不符）：在 `## 变更记录` 写明缺口，停下来向用户说明，等待用户补充或转 brainstorm。
- **环境阻塞**（依赖、权限、外部服务）：说明哪条验证无法执行、为什么，等待用户处理；不要把跑不了的命令改记成 judge/human。
- **非阻断性漂移**（实现中发现 PRD 过期但不卡住：版本号、API 形态、依赖兼容）：在 `## 变更记录` 回写"实际用了什么 + 为什么"再继续，不要默默改了代码却让 PRD 停在旧事实。选依赖/锁版本这类易过期事实，先查证当前稳定版，不靠回忆。
- **反复失败的根因分析**：同一 failing check 反复 3 次未过 → 停止盲改，进根因分析（复现 → 定位根因 → 假设 → 验证）再回来，不在失败循环里盲目修改耗 context。

## 结束

所有 slice 完成后：汇总本次改动范围与证据位置。review 已在每个 slice 执行，无需额外触发。
