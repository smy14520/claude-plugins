---
name: "Knowledge Conflict: develop 访谈推翻已有 ADR"
description: "单技能测试：经 /develop 提出与已有 ADR 相悖的修改并给出新事实（todo-sync 已改按 updated_at 同步），考察访谈中是否指出与 ADR-0001 的冲突，并在确认后原地改写 ADR（附原为…的一行）"
type: single-skill
initial_command: '/develop "把 todo 的 id 改成 uuid。todo-sync 上周已经升级了，现在按 updated_at 做增量同步。"'
setup_project: false
max_turns: 15
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- `.forge/wiki/decision/0001-integer-ids.md`（ADR）规定 id 必须是单调递增整数，理由是 todo-sync 以 max(id) 做同步水位线。
- 用户给出新事实：todo-sync 已改按 updated_at 同步。ADR 的前提不再成立。

## 2. 期望行为
- 访谈或实现前读到 ADR-0001，并指出它与本次决定冲突。
- 用户确认后，原地改写 ADR-0001：正文陈述现行决定（id 用 uuid），末尾一行说明原为递增整数、因 todo-sync 改按 updated_at 同步而改；不追加修订块，不另建一份旧全文。
- 代码改为 uuid（新任务用 uuid；旧数据兼容方式在访谈中定），测试全绿，commit。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1~2 句），按推荐答案拍板。
- 旧数据：已有整数 id 原样保留，只有新任务用 uuid；`done` 命令接受两种 id。
- 被问到 ADR 冲突时，回答"以现在为准，ADR 按现状改"。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否主动发现并指出 ADR 冲突？
- ADR 是否原地改写为现行决定并附一行"原为…"？
