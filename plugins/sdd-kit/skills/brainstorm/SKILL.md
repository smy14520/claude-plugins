---
name: brainstorm
description: "把需求、当前 repo 上下文和用户偏好收敛为 executable package PRD，或把过大的 initiative 路由到 `.arbor/maps/<initiative>/` 并 materialize child package stubs。Brainstorm 是需求明确与 package boundary 判断阶段；不拆 T-xxx、不写代码。仅在用户显式请求时激活。"
---

# Brainstorm — Requirement to PRD / Package Boundary

Brainstorm 是把需求真正落到 PRD 和 package boundary 的阶段。Research 可以提供材料，但不是前置必需；没有 research 时，Brainstorm 仍要结合当前 repo、用户输入和必要澄清来收敛需求。

```text
research? → [brainstorm]
              ├── single package: .arbor/tasks/<package>/prd.md → task
              └── large initiative: .arbor/maps/<initiative>/map.md + map.json + child package stubs
```

## 职责边界

- 明确需求：背景、目标、范围、场景、验收关注点、开放问题。
- 理解当前 repo：现有实现、源码/测试布局、运行方式、约束；不要把 `.arbor/tasks/<package>/` 当产品源码目录。
- 和用户澄清真正影响实现的选择：技术栈、架构风格、数据/权限/交易语义、目录与测试偏好。
- 区分约定的归属：
  - 全局项目约定：先询问用户是否沉淀到 `CLAUDE.md` 或 `.claude/rules`。
  - package-local 约束：写入当前 package PRD。
- 决定 package boundary：一个 branch/worktree/PR 可完成的进 `.arbor/tasks/<package>/`；需要多个执行边界的进 `.arbor/maps/<initiative>/`。
- 不采集 raw evidence（research）、不拆 T-xxx（task）、不写代码（impl）、不做语义审计（review）。

## Route decision

先理解上下文和关键选择，再 route。不要因为用户一句大需求就机械按业务名拆，也不要在边界不清时直接创建一堆 package。

### 1. Single executable package

当前 change 可用一个 branch/worktree/PR review、回滚和交付：

```text
python3 plugins/sdd-kit/tools/arbor.py create <package> --mode strict-atomic --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py set-package-sizing <package> --status fits_package --actor brainstorm --phase brainstorm --decision "single executable package boundary is valid"
```

然后写/更新 `.arbor/tasks/<package>/prd.md`。

### 2. Large initiative / package graph

当前主题需要多个 package / PR / worktree / 发布节奏：

```text
python3 plugins/sdd-kit/tools/arbor.py create-map <initiative> --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py create-split-packages <initiative> \
  --package "<package>::<title>::<dep1,dep2>::<boundary reason>" \
  --actor map \
  --decision "package graph materialized from .arbor/maps/<initiative>/map.md"
```

Map 只保存 package graph、依赖、execution waves 和必要的 implementation framing。child package stub 可立即 materialize；T-xxx 仍由 package-local task 阶段生成。

如果当前 repo 还没有实现基线，Brainstorm 应自然先和用户确认项目级选择，并把“建立项目基线/脚手架”作为可执行 package 之一，而不是让多个业务 package worker 各自发明技术栈。

### 3. Package extracted from map

当前 package 已存在于 `.arbor/tasks/<package>/`，且：

```text
package_sizing.status = split_applied
prd.parent_map = .arbor/maps/<initiative>/map.md
```

此时只补全该 package 的 `prd.md`，不修改 sibling package 状态。

## PRD 内容

使用 `assets/templates/prd.md`。PRD 服务后续 task decomposition，不追求堆砌完整合同。

应写清：

- 背景与问题。
- 目标 / Desired outcomes。
- In scope / Out of scope。
- 关键场景与边界场景。
- 交付物清单。
- 高层方案草图与实现切片线索。
- Boundary sizing decision：为什么这是一个 executable package，或为什么 route 到 map。
- 关键约束：只保留会影响 task 拆解或实现边界的约束。
- Sources：关键判断、场景、风险可追溯。
- Open questions / Assumptions / Risks 分开写。

来源 ID 约定：

```text
SRC-RES-001   research note/raw
SRC-LOCAL-001 本地文件 / 代码位置
SRC-EXT-001   外部 URL
```

机器可读来源追加到 `context/sources.jsonl`：

```text
python3 plugins/sdd-kit/tools/arbor.py add-context <package> --type sources --source-id SRC-LOCAL-001 --source-type local-file --location "src/...:12-48" --title "<title>" --why "<why>"
```

## Forward-only amendment

当用户说某个已进入 task/impl/review 的 package 需求不对，或 review 返回 `BRAINSTORM_DRIFT`：

1. 判断修正是否仍在当前 package boundary 内；若影响 sibling / package graph，停止并回 map/user。
2. 不静默改写旧需求、不重排旧 T-xxx。
3. 在 `prd.md` 的 `Amendments / Forward-only corrections` 追加 `AMD-xxx`，写清 wrong / correct / affects / source。
4. 同步机器状态：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py add-amendment <package> --title "<title>" --wrong "<old>" --correct "<new>" --affects-task T-003 --actor brainstorm
   ```
5. 输出下一步：用 task 为该 AMD 追加新的 T-xxx。

## Finalize

当用户要求 “brainstorm 定稿 / 可以进入 task / finalize brainstorm” 时：

1. 确认没有会阻塞 task 拆解的 open question。
2. 确认 `Boundary sizing decision` 是 `fits_package` 或 `split_applied`。
3. 将 PRD frontmatter `status` 置为 `ready-for-task`。
4. 更新机械状态：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py set-prd-status <package> --status ready-for-task --actor brainstorm --note "prd ready for task"
   ```
5. 输出结稿摘要，不自动调用 task。

## 核心原则

1. Brainstorm 不是填模板；它负责把需求和 repo 现实对齐。
2. 少即是多；不要用额外文件和规则替代思考、澄清和正确拆边界。
3. 全局约定先问用户是否落库；局部约束写 PRD。
4. Package 是执行边界；T-xxx 是 package-local control / acceptance / review 单元。
5. `.arbor/` 是控制面；产品源码/测试写在 repo implementation tree。
6. 修正走 amendment；不重写历史 PRD/task。
7. 不自动推进；`ready-for-task` 是状态，不是触发器。

## 停止并回报

- 需求仍在发散，不足以定 package boundary。
- 技术栈、架构、目录、测试方式等选择会影响多个 package，但用户尚未确认。
- 需要用户决定产品/权限/交易/金额/退款等语义。
- package boundary 会影响 sibling package lifecycle。

## 入口

- 用户入口：`/sdd-kit:brainstorm`
- 输出：`.arbor/tasks/<package>/prd.md` 或 `.arbor/maps/<initiative>/map.md` + `map.json`
