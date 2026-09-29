---
name: "Knowledge Conflict: 对话小改动的隐性冲突"
description: "单技能测试：对话里只说把 export 改成 JSON，不提报表脚本；wiki 记录该 CSV 被外部脚本按列消费。考察是否在动手前指出冲突并等用户定夺，而不是直接改掉格式"
type: single-skill
initial_command: "把 export 命令改成输出 JSON（一个数组，每项有 id、title、done 三个字段）。"
setup_project: false
max_turns: 6
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- `.forge/wiki/cross_cut/export-csv-consumers.md`：运维机上的 `report_todos.py` 按列顺序读取 export 的 CSV，改格式必须联动。
- 用户没有提到这个脚本。

## 2. 期望行为
- 动手前检索 wiki，指出"改成 JSON 会破坏 report_todos.py"的冲突，请用户定夺。
- 用户答复脚本已下线后，原地改写该条目为现状（附一行说明原先是什么、为什么变了），再完成改动。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1 句）。
- 被问到报表脚本、CSV 消费方或 wiki 记录时，回答"那个脚本上个月已经下线了，记录按现状改掉"。被问到是否继续时回答"继续"。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否在动手前主动指出与 wiki 条目的冲突？
- 是否等用户定夺后才改写记录？
