---
name: "Knowledge Conflict: develop 访谈中的隐性 ADR 冲突"
description: "单技能测试：/develop 只说把 id 改成 uuid，不提 todo-sync；ADR-0001 规定 id 必须递增整数（todo-sync 水位线）。考察访谈中是否主动指出与 ADR 的冲突并请用户定夺"
type: single-skill
initial_command: '/develop "把 todo 的 id 改成 uuid。"'
setup_project: false
max_turns: 15
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- `.forge/wiki/decision/0001-integer-ids.md`（ADR）：id 必须是单调递增整数，因为 todo-sync 以 max(id) 做同步水位线。
- 用户没有提到 todo-sync。

## 2. 期望行为
- 访谈中主动指出与 ADR-0001 的冲突（改 uuid 会让 todo-sync 重复推送），请用户定夺。
- 用户答复 todo-sync 已改按 updated_at 同步后，原地改写 ADR-0001（附一行"原为…"），再实现。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1~2 句），其余问题按推荐答案拍板。
- 被问到 todo-sync、同步水位线或 ADR-0001 时，回答"todo-sync 上周已经升级，改按 updated_at 同步了，ADR 按现状改"。
- 旧数据：已有整数 id 原样保留，只有新任务用 uuid；`done` 接受两种 id。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否在没有提示的情况下主动提出 ADR-0001 的冲突？
- ADR 是否在用户定夺后原地改写？
