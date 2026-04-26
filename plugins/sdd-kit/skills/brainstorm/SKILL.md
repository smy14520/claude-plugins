---
name: brainstorm
description: "在创建 task package 前做边界路由：将需求收敛为可执行 package PRD `.arbor/tasks/<package>/prd.md`，或把大 initiative 路由到 `.arbor/maps/<initiative>/map.md` + `map.json` 并 materialize child package stubs。仅在用户显式请求时激活。"
---

# Brainstorm — Boundary Routing + Executable Package PRD

Brainstorm 的职责是把一次 change 收敛到**可执行 package 边界**：

- 如果是单个可执行 package：创建/维护 `.arbor/tasks/<package>/prd.md`。
- 如果是 large initiative：不要创建 `.arbor/tasks/<initiative>/`，改为创建/更新 `.arbor/maps/<initiative>/map.md` + `map.json`，并立即 materialize child package stubs：`.arbor/tasks/<package>/`。
- 如果是从 map 拆出的子 package：使用已 materialize 的 `.arbor/tasks/<package>/prd.md` 继续 package-local brainstorm，并保留它来自上位 map 的记录。

`.arbor/tasks/<package>/` 是 branch/worktree/PR/agent ownership 执行边界；package 内的 T-xxx 后续只是 control / acceptance / review 单元。

```text
research → [brainstorm]
              ├── small/medium: .arbor/tasks/<package>/prd.md → task
              └── large:       .arbor/maps/<initiative>/map.md + .arbor/tasks/<child-package>/ stubs
```

**不做什么**：不采集素材（research）、不拆 T-xxx（task）、不写代码（impl）、不自动 ingest wiki、不自动推进到 task。

## Boundary routing layer

Brainstorm 阶段不再创建 `.arbor/brainstorms/<name>.md`。也不要在确认边界前机械创建 `.arbor/tasks/<name>/`。

先做 route decision：

1. **single executable package**
   - 当前 change 可用一个 branch/worktree/PR review、回滚和交付。
   - 创建 `.arbor/tasks/<package>/`：
     ```text
     python3 plugins/sdd-kit/tools/arbor.py create <package> --mode strict-atomic --title "<title>"
     python3 plugins/sdd-kit/tools/arbor.py set-package-sizing <package> --status fits_package --actor brainstorm --phase brainstorm --decision "single executable package boundary is valid"
     ```
   - 写/更新 `prd.md`，finalize 时再设置 `ready-for-task`。

2. **large initiative / package graph**
   - 当前主题需要多个独立 package / PR / worktree / 发布节奏。
   - 不创建 `.arbor/tasks/<initiative>/`。
   - 创建/更新 `.arbor/maps/<initiative>/map.md` 与 `map.json`，列出 package graph、execution waves、跨 package contract，并提供机器可读 dependency/status/agent assignment context。
   - 立刻 materialize map 中的 executable package 节点，但不写 T-xxx：
     ```text
     python3 plugins/sdd-kit/tools/arbor.py create-map <initiative> --title "<title>"
     python3 plugins/sdd-kit/tools/arbor.py create-split-packages <initiative> \
       --package "<package>::<title>::<dep1,dep2>::<boundary reason>" \
       --actor map \
       --decision "package graph materialized from .arbor/maps/<initiative>/map.md"
     ```
   - 停止；child package 的详细 PRD 由后续 package-local brainstorm 填写，不要在 initiative 阶段写长 T-xxx 列表。

3. **package extracted from map**
   - 当前 package 是上位 map 中一个已确认并已 materialize 的可执行节点。
   - 读取 `.arbor/tasks/<package>/prd.md` 和 `task.json`，确认 `package_sizing.status=split_applied`。
   - `prd.md` 的 `Boundary sizing decision` 必须写明 parent map。

脚本只负责目录、模板和 `task.json` 初始化；PRD 正文仍由本 skill 写。若旧 `.arbor/brainstorms/<name>.md` 存在，只作为 legacy input 读取并提示迁入；关键结论必须显式摘要进 `.arbor/tasks/<package>/prd.md`，后续 task/impl/review 不得依赖旧路径。新写入不得再创建旧路径。

## 四个原语

### 🧭 Route — 判断 package boundary

触发："brainstorm 一下 X" / "写 brainstorm X" / "把这个需求收敛一下" / "先整理成 PRD"。

1. 命名（kebab-case，按主题，不含日期）。
2. 读取用户显式引用的 research / 本地文件 / URL，并提取当前有效结论。
3. 先判断 route：single executable package / large initiative / package extracted from map。
4. 若是 large initiative，创建/更新 `.arbor/maps/<initiative>/map.md` + `map.json`，并用 `create-split-packages` materialize child package stubs 后停止；如需统筹多 agent，只输出 `map-check` / `map-plan-agents` 结果，不自动执行。
5. 只有确认是 executable package 后，才创建 `.arbor/tasks/<package>/`；large initiative 只创建 child package，不创建 parent task package。

> 推理节奏：重度。这里决定后续 task 是否能直接拆，以及多 agent/worktree/PR 的实际边界。

### 🎯 Frame — 收敛问题与范围

1. 从 `assets/templates/prd.md` 生成或更新 `.arbor/tasks/<package>/prd.md`。
2. 填写：
   - 背景与问题
   - 目标 / Desired outcomes
   - 本次范围 / Out of scope
   - 关键场景
   - 交付物清单
   - `Boundary sizing decision`
3. `Boundary sizing decision` 必须能解释为什么这是一个 executable package，而不是 initiative。
4. 输出骨架摘要，必要时向用户提出 1-3 个最高杠杆问题。

### 📚 Ground — 绑定证据与拆解线索

触发：用户提供了 research / 代码 / URL，希望把它们真正写进 PRD；或 PRD 草稿仍然太空、无法直接拆任务。

1. 为每个关键来源分配稳定来源 ID：
   - `SRC-RES-001`：research note/raw
   - `SRC-LOCAL-001`：本地文件 / 代码位置
   - `SRC-EXT-001`：外部 URL
2. 将关键信息写入 `.arbor/tasks/<package>/prd.md`：
   - 方案草图 / Proposed approach
   - 拆解线索 / 实现切片建议
   - 关键约束（仅限真正承重的约束）
   - 验证重点
   - 风险 / 开放问题 / 假设
   - `## Sources`
3. 将机器可读来源追加到 `context/sources.jsonl`：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py add-context <package> --type sources --source-id SRC-LOCAL-001 --source-type local-file --location "src/...:12-48" --title "<title>" --why "<why>"
   ```
4. 允许存在开放问题，但必须区分：
   - `Open questions`：会影响 task 拆解的未决项
   - `Assumptions`：暂时成立、后续需验证的前提
   - `Risks`：即使继续拆任务也需要显式暴露的风险
5. 在正文关键判断旁用 `[SRC-...]` 标记来源，避免来源只埋在附录里。

### ✅ Finalize — 标记 ready-for-task

触发："brainstorm 定稿" / "可以进入 task 了" / "finalize brainstorm"。

1. 执行 `prd.md` 底部自检清单。
2. 若 `Boundary sizing decision` 不是 `fits_package` 或 `split_applied`，阻止定稿；large initiative 应回到 map。
3. 若仍存在会阻塞 task 拆解的开放问题，阻止定稿并列出位置。
4. 将 `prd.md` frontmatter `status` 置为 `ready-for-task`，写入 `date: today`。
5. 使用 helper 更新机械状态：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py set-prd-status <package> --status ready-for-task --actor brainstorm --note "prd ready for task"
   ```
   helper 会拒绝 `package_sizing.status=unchecked` 或 `split_recommended` 的 PRD。
6. 输出结稿摘要，不自动调用 task skill。

## 核心规则

1. **先 route，再 materialize** —— 不要为 large initiative 创建 `.arbor/tasks/<initiative>/`；large route 应创建 map，并把 child executable package 立即 materialize 成 `.arbor/tasks/<package>/` stub。
2. **以可拆解性为中心，而不是以 contract 完整性为中心** —— task 需要的是场景、范围、交付物、切片、顺序和局部上下文。
3. **来源是一等公民** —— 关键判断、场景、风险应能追溯到 research、代码或外部 URL。
4. **一个 executable package 一个 PRD** —— 如果需要多个 PR/worktree/branch，应拆 package，并用 map 维护导航。
5. **Package 是执行边界** —— PRD 必须说明本 package 的 branch/worktree/PR 边界；后续 T-xxx 只是 package-local control / acceptance / review 单元。
6. **允许保留开放问题，但必须显式分类** —— 不是所有未决项都会阻塞 task；真正阻塞的要标出。
7. **不自动推进** —— `ready-for-task` 只是一个状态，不是自动触发器。
8. **Wikilink 可选** —— 可作为 PRD 背景线索，但不能替代文档自解释；`task.md` 仍禁止 wikilink。
9. **新写入只写 package-local PRD 或 map** —— `.arbor/brainstorms/<name>.md` 仅 legacy fallback，不是新产物位置。

**长度**：目标 120-300 行。若 > 350 行且包含多个独立切片，优先 route 到 map，而不是继续扩写一个 package PRD。

## 何时不激活

- 简单修补 / 一行 bug → 直接 impl
- 仍在发散、还不知道问题是什么 → 先 research
- 已有有效 `task.md` 且用户只是想执行任务 → 直接 impl

## 输出位置

```text
.arbor/maps/<initiative>/map.md          # large initiative / package graph
.arbor/tasks/<package>/prd.md        # executable package PRD
```

## 入口

- 用户入口：`/sdd-kit:brainstorm`
- 输出位置：`.arbor/maps/<initiative>/map.md` 或 `.arbor/tasks/<package>/prd.md`
