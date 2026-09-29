---
name: "Wiki Impact: 评估改动影响时主动检索 wiki"
description: "单技能测试：普通对话中请求评估存储格式改动的影响，wiki 里预埋一条代码 grep 不到的仓库外联动（todo-sync / 报表任务），考察是否主动检索 wiki 并报出该联动"
type: single-skill
initial_command: "我想把 .todos.json 改成 {\"version\": 1, \"tasks\": [...]} 的结构，顺便把 id 换成 uuid。先别改代码，帮我评估一下这个改动的影响。"
setup_project: false
max_turns: 3
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 预埋事实
- 代码里 `.todos.json` 只被 `todo.py` 读写，仓库内看不到其他消费者。
- `.forge/wiki/cross_cut/todos-json-external-consumers.md` 记录了两个仓库外消费者：手机端同步服务 **todo-sync**（依赖顶层数组 + 递增整数 id 作为同步水位线）与月度报表 **report_todos.sh**（`jq '.[]'` 依赖顶层数组）。

## 2. 期望行为
- 评估前主动检索 `.forge/wiki`（调用 wiki skill 或读取 index / cross_cut 条目）。
- 影响评估中明确报出 todo-sync 与报表任务会受影响，以及 uuid 会让 todo-sync 的同步水位线失效。
- 不修改任何代码。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是提需求的开发者；回答简短（1 句）。被问到是否开始改代码时，回答“先不改，只要评估”。

## 2. 核心主观评价焦点 (Qualitative Focus)
- 是否在没有任何提示的情况下检索了 wiki？
- 是否报出了代码里看不到的仓库外消费者？
