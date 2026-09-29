---
name: "Knowledge Conflict: 对话小改动撞上过时 wiki 条目"
description: "单技能测试：不走 grill，在对话里直接提小改动并顺口给出新事实（报表脚本已下线），考察实现前是否检索 wiki、是否指出与 cross_cut 条目的冲突，并在确认后原地改写该条目"
type: single-skill
initial_command: "把 export 命令改成输出 JSON（一个数组，每项有 id、title、done 三个字段）。对了，运维机上那个月度报表脚本上个月已经下线了。"
setup_project: false
max_turns: 6
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- `.forge/wiki/cross_cut/export-csv-consumers.md` 记录：运维机上的 `report_todos.py` 按列顺序读取 export 的 CSV，改格式必须联动。
- 用户在需求里给出了新事实：该报表脚本已经下线。这与 wiki 条目矛盾。

## 2. 期望行为
- 实现前检索 `.forge/wiki`，读到 export 相关的 cross_cut 条目。
- 指出该条目与用户所说"脚本已下线"矛盾，并在用户确认后原地改写（或删除）该条目，说明原先是什么、为什么变了；index 同步。
- export 改为输出 JSON 数组，测试随之更新并全绿。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1 句）。
- 被问到报表脚本或 wiki 记录时，回答"脚本确实下线了，记录按现状改掉"。被问到是否继续时，回答"继续"。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否在没有提示的情况下检索了 wiki 并发现了冲突？
- 过时条目是否被原地改写为现状，而不是保留旧说法或追加修订块？
