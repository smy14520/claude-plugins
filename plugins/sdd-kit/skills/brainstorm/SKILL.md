---
name: brainstorm
description: "仅当用户显式请求 /sdd-kit:brainstorm、用 brainstorm skill、normal/grill/grill-me 需求收敛，或要求在 task/map 前收敛需求/PRD 时使用。不要用于 research 收集、map 拆包、task 拆解、impl 或 review。"
---

# Brainstorm — 需求澄清 / Design Framing

Brainstorm 把用户目标、repo 现实和已有 research 收敛成可执行前的需求与设计 framing。需求或实现前提不清楚时，不能拆包。

```text
research? → [brainstorm]
              ├─ small: single package PRD → task
              └─ large: clarified initiative framing → map → package-local brainstorm → task
```

## 入口模式

如果用户显式指定 `normal`、`grill` 或 `grill-me`，直接使用该模式。否则在开始前用 `AskUserQuestion` 让用户选择：

- `normal`：默认模式，高效收敛；只问当前最影响设计、package boundary、task 拆解或 map handoff 的问题。
- `grill`：压力测试模式；沿 plan/design decision tree 逐支追问，解决决策依赖，直到 shared understanding；每个问题都给推荐答案。

两种模式都必须先读 repo / research / 相关 PRD/map；能由代码或已有材料回答的问题不要问用户。

## 工作循环

1. **Context first**：先读 repo、已有 research、用户输入、相关 PRD/map；能从上下文确认的不要问。
2. **State understanding**：简要说明已知事实、当前理解、真正会影响方向的缺口。
3. **One useful question**：normal 只问最高价值阻塞问题；grill 沿 decision tree 一次问一个问题，并给推荐答案与理由。
4. **Right place**：全局项目约定经用户同意后沉淀到 `CLAUDE.md` / `.claude/rules`；initiative/package-local 约束写入 framing 或 PRD。
5. **No silent split**：需求和 implementation framing 都清楚后，才进入出口判断。

## Map readiness gate

`research.status=ready-for-brainstorm` 只表示已有材料足够进入 brainstorm；不表示可以直接进入 map。Research 可能只澄清了业务范围，尚未澄清实现前提。

Large initiative handoff 前，必须确认足以支撑 package graph 的 implementation framing：

- repo 现实：已有源码/测试/运行方式，或明确缺少产品实现面。
- 项目形态：应用类型、技术栈、前后端关系，或明确先用 baseline/scaffold package 承载这些选择。
- 跨 package 语义：数据持久化、权限、交易、状态流转、验收口径。
- 工程约定：源码/测试布局、运行/验证方式、需要沉淀的全局规则。

如果这些缺口会影响多个 package，不要输出 map handoff；继续提问。不要把“map 阶段不要默认技术栈”当作替代提问。

## 出口

### 1. 仍不清楚

如果缺少会影响设计或执行边界的信息：

- 输出当前理解和缺口。
- 问一个高价值问题，带具体选项/权衡/推荐。
- 不创建 package，不创建 map，不写 package graph。

典型缺口：项目形态、MVP 边界、核心用户流、权限/交易语义、数据持久化、测试与运行方式。

### 2. Single executable package

当前 change 可用一个 branch/worktree/PR review、回滚和交付时：

- 创建或更新 `.arbor/tasks/<package>/prd.md`。
- 记录 package sizing 为 `fits_package`，actor/phase 为 `brainstorm`。
- PRD 写清：背景、目标、scope、关键/边界场景、交付物、高层方案、boundary decision、关键约束、sources、open questions / assumptions / risks。

### 3. Large initiative → map

需求和 implementation framing 都清楚，且自然包含多个 executable packages / PR / worktree / 发布节奏时：

- 只输出 clarified initiative framing。
- 不运行 map 创建命令。
- 不 materialize child package stubs。
- 不创建 `.arbor/tasks/<child-package>/`。

Handoff 写清：目标/MVP、repo 现实与实现前提、已确认的项目级选择、角色与核心流、关键规则/风险、为什么需要 map、拆包顺序线索（baseline/shared contract/上游下游依赖）、仍不阻塞 map 的局部问题。

下一步提示：`/sdd-kit:map <initiative>`。

### 4. Map-derived child package

当 `.arbor/tasks/<package>/` 已由 map materialize，且 `package_sizing.status=split_applied` / `prd.parent_map` 指向 map：

- 继承 map 中已确认的 initiative-level framing。
- 只补 package-local 场景、交付物、约束、验证重点。
- 不修改 sibling package 状态。
- 若发现全局 framing 已失效，停止并回 map/user。

## Arbor state

`arbor.py` 只做机械状态维护；语义判断写在 PRD/framing 中。需要精确参数时运行：

```text
python3 plugins/sdd-kit/tools/arbor.py <subcommand> --help
```

Brainstorm 常用 subcommands：

- `create`
- `set-package-sizing`
- `add-context`（sources）
- `add-amendment`
- `set-prd-status`

## Amendment / finalize

- 已进入 task/impl/review 后发现需求错了：只做 forward-only amendment；package-local 修正追加 `AMD-xxx` 并记录 `add-amendment`。若影响 sibling 或 package graph，停止并回 map/user。
- Finalize 只适用于 single package PRD 或 map-derived child PRD：无阻塞 open question，boundary 为 `fits_package` 或 `split_applied`，再将 PRD 置为 `ready-for-task`。
- Large initiative framing 不走 `ready-for-task`；下一步是 map。

## 不做

- 不采集 raw evidence（research）。
- 不创建/维护 package graph，不创建 map，不 materialize child stubs（map）。
- 不拆 T-xxx（task）。
- 不写代码（impl）。
- 不做语义审计（review）。
- 不自动推进下一阶段。
- 不把产品源码/测试写到 `.arbor/`。
