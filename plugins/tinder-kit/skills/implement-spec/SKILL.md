---
name: implement-spec
description: "把 to-spec 与 to-tickets 的产物整体落地：tickets 作为 task graph，在各自 worktree 中并行实现，合入一个 integration branch。在 spec 已拆成带 blocking edges 的 tickets、要一次落地整个 spec 时使用。"
---

你拿到的是一份 spec，它应当已经拆成了 tickets，描述如何实现这份 spec。

Issue tracker 应该已经提供给你；如果缺少 `.forge/issue-tracker.md`，请让用户运行 `/setup`。

目标是整份 spec 实现在同一个 **integration branch** 上，且每张 ticket 都按 issue tracker 的方式 resolve。

spec 与 tickets 是行为要求的依据；笔记和实现都不改写它们。

Tickets 不是步骤清单，而是带 blocking 关系的 **task graph**。因此任何时刻都存在一个可以立即开工的 **frontier**。

与 subagents 之间的沟通要稀疏，主要通过 **context pointers**：spec、tickets、research notes 以及之前的 commits。已经能通过 pointer 拿到的信息不要重复转述。`.forge/` 下的 pointer 一律写成主 checkout 的绝对路径——`.forge/` 可能被 gitignore，worktree 里看不到它；主 checkout 的 `.forge/` 就是所有 subagent 共享的那一份进度。

**Implementer subagents** 尽可能在后台运行，以获得最大并发。

## Steps

1. 读 spec 和 tickets，理解 task graph。

2. （可选）用一个 **exploration subagent** 完成 tickets 需要的探索——相关代码或外部文档。让它把 markdown 笔记写到主 checkout 的 `.forge/<feature-slug>/` 下，供之后所有 subagent 读取。这样 **implementer subagents** 能专注实现而不是探索。多张 frontier tickets 会碰同一个共享面（同一个 config、type、文案目录）时，在笔记里先定下各自要新增的确切名字。

3. 创建 integration branch。如果 issue tracker 通过 PR 关闭工作，或用户要求 PR，在 step 5 第一次合并之后开 draft PR（没有领先 main 的 commit 时开不了），标记为关闭该 spec 与 tickets。

4. 为每张 ticket 派一个 **implementer subagent**，各自在自己的 worktree 和 branch 上工作。每个 implementer subagent：
   - 开工前确认自己的 worktree 基于 integration branch，否则先 reset 到它上面；
   - 调用 `tdd` skill 构建这张 ticket，把工作 commit 到自己的 branch，commit message 引用 ticket 路径；
   - 报告完成前，把 integration branch 的最新 tip 合入自己的 branch。

   验证依赖未跟踪材料（gitignored 的 fixtures、本地数据库、凭据）的 ticket，在 worktree 里会静默跳过关键测试——这类 ticket 安排在主 checkout 上单独执行。

5. 一个 **implementer subagent** 完成后，用一个 **merger subagent** 把它的工作合入 integration branch。合入后 resolve 这张 ticket。

6. 如果这改变了 **frontier**，为新解锁的 tickets 启动更多 **implementer subagents**，保持最大并发。Ticket 状态只由你（orchestrator）写入主 checkout 的 `.forge/`，implementer 不改 tracker。

7. 全部 tickets 完成后，以 integration branch 的起点为 fixed point 调用一次 `tinder-kit:code-review`。Standards findings 与未满足的 ticket 验收项交给一个 **implementer subagent** 修复，修复后只做聚焦验证。其余 Spec findings（scope creep、spec 自相矛盾、你认为不该照做的要求）不自行裁决，列入交付汇报交给用户。

8. 如果存在 draft PR，把它标记为 ready for review；否则汇报 integration branch。

9. 清理所有 **implementer subagent** 的 worktrees。
