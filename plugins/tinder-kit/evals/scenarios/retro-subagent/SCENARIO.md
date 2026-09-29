---
name: "Retro: 从子 agent 记录中提取候选，只写用户选中的"
description: "单技能测试：先派两个 subagent 并行修两个测试（各踩一个 Python 坑：str.isdigit 接受上标数字、round 银行家舍入），要求它们只用一句话汇报；再调用 /retro。考察 retro 能否从子 agent 记录捞出两个坑、只写用户选中的那一条、此前不写 wiki"
type: single-skill
initial_command: "tests 里有两个失败的测试。派两个 subagent 并行各修一个（一个修 parse_qty，一个修 half_up），修完各自只用一句话汇报“修好了/没修好”，不要解释原因。都修好后跑全量测试并 commit。"
followup_command: "/retro"
setup_project: false
max_turns: 10
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- `parse_qty` 用 `str.isdigit()` 校验，但 `"²".isdigit()` 为 True 而 `int("²")` 抛 ValueError——Python 的 Unicode 数字坑。
- `half_up` 用内置 `round()`，而 `round(2.5) == 2`（银行家舍入）——Python 的舍入坑。
- 两个 subagent 被要求只用一句话汇报，坑的细节只在它们自己的会话记录里。

## 2. 期望行为
- 第一段：两个测试修好、全绿、commit；**此阶段不写 `.forge/wiki/`**。
- `/retro`：列出候选，至少包含这两个 Python 坑（附复现命令），每条说明来自会话的哪一刻、建议放哪一层；等用户选择。
- 用户只选 isdigit 那一条：只写 `.forge/wiki/gotcha/` 下这一条并更新 index；不写 round 那条。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是项目负责人；回答简短（1 句）。
- 第一段中被问到是否继续时回答“继续”。
- retro 列出候选后，回答“只写 isdigit 那一条，其他都不要”。

## 2. 核心主观评价焦点 (Qualitative Focus)
- retro 的候选是否来自这次会话的具体时刻（包括子 agent 内部发现的坑），而不是泛泛的建议？
- 是否只写了用户选中的条目？
