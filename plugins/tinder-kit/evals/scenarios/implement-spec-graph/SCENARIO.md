---
name: "Implement-Spec: task graph 并行落地 (Single-Skill)"
description: "单技能测试：预置 spec 与 4 张带 blocking edges 的 tickets（.forge 被 gitignore），考察 /implement-spec 能否按 frontier 在 worktree 中并行实现、合入 integration branch、合并后 resolve 并推进 frontier"
type: single-skill
initial_command: '/implement-spec .forge/inventory/spec.md'
setup_project: false
max_turns: 15
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 输入
- Spec：`.forge/inventory/spec.md`；Tickets：`.forge/inventory/issues/01..04`。
- Task graph：01 add、02 remove、03 list 无 blocker，构成初始 frontier；04 report 被 01、03 阻塞。
- `.forge/` 在 `.gitignore` 中，worktree 里不存在，只能通过主 checkout 的绝对路径读取。

## 2. 期望交付
- 一个 integration branch 承载全部工作；本地 tracker，不开 PR。
- 01、02、03 各由一个 implementer subagent 在独立 worktree / branch 中实现并 commit，commit message 引用 ticket 路径。
- 每合入一张 ticket 就把它的 `Status:` 置为 `resolved`；01 与 03 都合入后才启动 04。
- 04 的 report 复用 list 的格式化函数。
- 全部完成后对 integration branch 跑一次 code-review，修复 findings。
- `python3 -m pytest -q` 全绿；四个命令的行为符合各 ticket 验收项。
- 验收项逐字兑现：ticket 01 要求 `stock add x abc`、`stock add x 0` 都走 stderr 报错、退出码 1、库存不变（不是 argparse 的退出码 2）。
- code-review 中未满足的验收项被修复；其余需要取舍的 Spec findings 出现在最终汇报里交给用户，而不是由 orchestrator 自行裁决。
- 结束时 implementer worktrees 已清理。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是 spec 的作者，spec 和 tickets 已经定稿；回答简短（1~2 句）。
- 被问到要不要开 PR 时，回答“不用，停在 branch 上”；被问到是否继续时，回答“继续”。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **并发**：01/02/03 是否同时派发，而不是一张一张串行？
- **Frontier 推进**：04 是否在 01、03 合入后才开始？
- **Ticket 状态**：状态是否只由 orchestrator 写入主 checkout 的 `.forge/`？
- **合并质量**：三张票都改 `stock/cli.py`，冲突是否被正确处理、没有丢掉任何子命令？
- **收尾**：code-review 是否只在最后跑一次，worktrees 是否被清理？
