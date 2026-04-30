---
name: task
description: "Decompose an already boundary-sized executable package PRD `.arbor/tasks/<package>/prd.md` into package-local T-xxx control/acceptance/review units. Task is a secondary guard: it refuses unchecked or split_recommended package sizing and only proceeds for fits_package/split_applied. `.arbor/tasks/<package>/` is the package boundary; T-xxx tasks are not default branch/PR units. Invoke only on explicit user request."
---

# Task — Secondary Guard + T-xxx Decomposition

Task 将已确认的 executable package PRD 拆成执行者可直接推进的 package-local T-xxx。它不决定 package 边界，不写代码，不做审计。

```text
research? → brainstorm → map? → package brainstorm → [task] → impl → review
                                           │           │
                                           │           └─ task.md + task.json + context/*.jsonl
                                           └─ .arbor/tasks/<package>/prd.md
```

## 职责边界

Task 只处理 `.arbor/tasks/<package>/`：

- 输入：`prd.md` + `task.json` + 已记录的 `package_sizing`。
- 输出：写实 `task.md`、结构化 `task.json.tasks[]`、`context/*.jsonl`、冻结 definition。
- Package 是需求/评审/回滚边界。
- T-xxx 是 package-local control / acceptance / dependency / review 单元。
- 如果某个 T-xxx 需要独立交付边界，应回 map 拆成新 package。

详细拆解准则按需读：

```text
skills/task/references/workflow.md
skills/task/references/decomposition.md
skills/task/references/anti-patterns.md
```

## 必须先做的 secondary guard

读取 `.arbor/tasks/<package>/task.json`，检查：

```text
package_sizing.status
```

继续条件：

- `fits_package`：当前 PRD 已被确认为单个 executable package。
- `split_applied`：当前 package 是 map 拆出的 child executable package。

停止条件：

- `unchecked`：先回 brainstorm 澄清为 package PRD，或回 map 记录已澄清后的 boundary decision。
- `split_recommended`：先回 map，维护 `.arbor/maps/<initiative>/map.md` + `map.json` 并 materialize child packages。
- PRD 仍有阻塞 task 拆解的 open questions。
- 当前输入明显仍是 large initiative。

若 task 阶段发现上游 sizing stale（多业务域、T-xxx 预计超过约 8-10 个、前台/后台/交易/营销等明显分域），停止并回 map，不要硬拆长任务列表。

## 执行流程

1. 确定 package name 和输入源：首选 `.arbor/tasks/<package>/prd.md`；legacy `.arbor/brainstorms/<name>.md` 只可读取并摘要迁入 PRD。
2. 运行/读取 arbor helper 的 package summary（`show`）。
3. 通过 secondary guard 后，选择模式：
   - `strict-atomic`：默认，每个 T-xxx 尽量 ≤ 4h，单一交付物。
   - `lean`：更粗，适合单人快速推进。
4. 设计 milestone / DAG：共享能力先行，消费任务显式 `depends-on`，不得有环。
5. 输出轻量并行提示：按 `role` 聚合 lane，给出 suggested waves、shared/contract 前置任务和 ownership notes；这些只服务人工 / Team Auto / 多会话分工，不是 scheduler runtime。
6. 必要时写明 test strategy / test seam：observable behavior、适合的测试层级、外部边界 fake/sandbox、UI browser verification；task 只铺路，不执行 TDD。
7. 为每个 T-xxx 写入：
   - `id` / `milestone` / `role`
   - `title` 使用封闭动词：`CREATE | ADD | SET | DELETE | REPLACE`
   - `deliverable`
   - `depends-on`
   - task-local `context`
   - `sources`
   - `ready-check`
   - 可执行 acceptance（二元谓词或命令）
7. 写实 `.arbor/tasks/<package>/task.md`，不要留下模板占位。
8. 用 arbor helper 维护机械状态：`add-child`、`add-context` / `add-context-batch`、`freeze-definition`、`validate`；参数以 `<subcommand> --help` 为准。
9. 如果 validation 失败，修 `task.md` / helper 状态后再交付。

## Amendment append mode

当 PRD 出现新的 `AMD-xxx`：

1. 只追加下一个未使用的 T-xxx，不重排、不改写旧 T-xxx。
2. 新任务必须写明 `source-amendment: AMD-xxx`，必要时写 `corrects: [T-003]`。
3. 用 arbor helper 追加机器状态（`add-child`，带 `source-amendment` / `corrects`）。
4. 若旧 T-xxx 因 AMD 失效，先追加修正任务，再把旧任务标记为 `skipped` 并说明原因。
5. 新任务 acceptance 必须包含 corrected increment + regression checks。

`definition.frozen` 表示已有 T-xxx 定义稳定；不禁止 task skill 为 AMD 追加新 T-xxx。

## `task.md` 最小 contract

`task.md` 必须自包含，执行者不应回 PRD 猜高层决策。至少包含：

- package 概览、boundary sizing decision、parent map（如有）。
- milestone 列表。
- 依赖图 / 关键路径。
- 并行执行提示：role lanes、suggested waves、shared/contract 任务、ownership notes。
- T-xxx 列表，字段齐全。
- 每个 T-xxx 的 acceptance 可执行。
- 必要时说明 test strategy / test seam，但不把 TDD 变成独立阶段。
- sources 可追溯。

禁止：

- wikilinks 作为执行依赖。
- wiki 页面作为未验证 source of truth；可以作为背景提示，但 `task.md` 必须自包含。
- “决定/调研/设计某方案”这类开放任务。
- 重排已有 T-xxx 编号。
- 为 T-xxx 默认写 branch/PR。
- 只调用 `sdd-arbor add-child` 而不把真实任务写入 `task.md`。

## 状态源规则

- `task.json` 是 lifecycle source of truth。
- `sdd-arbor add-child` 只更新 `task.json`，不会同步 Markdown。
- `task.md` 是稳定任务定义，impl/review 不修改；task skill 只可 append AMD 对应的新 T-xxx。
- `review.md` 是追加审计日志，不是当前状态源。
- 不创建 `status.md`。
- context JSONL 是索引，不是长文档；通过 `add-context` / `add-context-batch` 写入，不手写文件。

## 完成条件

Task 完成时应满足：

- `task.md` 无模板占位。
- `task.json.tasks[]` 与 `task.md` 的 T-xxx 对齐。
- amendment task 已和 `source_amendment/corrects` 对齐（如适用）。
- definition frozen。
- `sdd-arbor validate <package>` 通过。
- `next_action.skill` 指向 `impl` 或在阻塞时明确指向 `user` / `brainstorm` / `task`。

## 本 skill 不做

- 不创建 large initiative 的 `.arbor/tasks/<initiative>/`。
- 不重新做 package boundary 判断。
- 不写代码、不运行 impl、不 review。
- 不创建 branch/PR；只可记录 package-level metadata。
- 不自动推进到下一个 skill。
