---
name: "Knowledge Conflict: 无冲突对照"
description: "单技能测试：与 wiki 记录无关的小改动（list --all），考察不会因冲突规则多做任何事：不改 wiki、不追问无关记录"
type: single-skill
initial_command: "给 list 命令加一个 --all 参数，同时显示已完成的任务，已完成的在末尾标 [done]。"
setup_project: false
max_turns: 5
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 期望行为
- 实现 `list --all`，测试全绿。
- 不修改 `.forge/wiki/` 下任何文件，不就 ADR-0001 或 export 条目追问用户。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1 句）。被问到是否继续时回答"继续"。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否只做了被要求的事，没有因 wiki 记录产生多余动作？
