---
name: review
description: "审计一个 seed-kit 任务的实现：读 PRD + diff + evidence，逐条 AC 对账并专查偷懒签名。每个 slice 的 assert 验证后自动触发，处理 [judge] 义务（选择 Mode 1/2/3 评分）并做语义审计。结论追加到 review.md。不改代码、不改需求、无状态流转。"
---
# Review — 语义审计

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

用干净视角审计实现是否兑现了 PRD 承诺。生成者 ≠ 验证者：不要依赖 impl 过程的叙述，只看 PRD、代码 diff 和落盘证据。

## 输入

1. `.arbor/tasks/<task>/prd.md` + `slices/S-NNN.md` —— 逐条 AC 和每个 slice 的验收。
2. 代码 diff —— base 由用户指定；未指定时从 git log 推断本任务起点并向用户确认。
3. `seed status <task> --json` + `evidence/` —— 核对每条验证的真实执行记录（命令、exit_code、输出）。

## 对账

先读项目的 `CLAUDE.md`、`.claude/rules/`、`DESIGN.md`——这些是项目的硬规则和审美标准。对账时专查：
- **规则违反**：实现是否违反 `.claude/rules/` 里的测试纪律（如 UI 没写交互测试、覆盖率不够）？
- **设计偏离**：视觉/交互是否偏离 `DESIGN.md` 的设计语言（如配色、字体、组件风格）？
- **CLAUDE.md 约束**：是否违反 `CLAUDE.md` 的项目级约束（如”不要自动 commit”、”用中文写注释”）？

项目无这些文件时，按 PRD 的质量基线与通用可交付地板判断。

- 每条 AC 映射到具体代码/测试：在哪里实现、哪条证据证明它成立，包括失败路径。
- 每个行为变更映射回 AC；多余的“顺手改进”按漂移记录。
- 专查偷懒签名：弱化或删除的断言、吞掉的异常、抄实现的假测试、新增 lint/类型抑制注释、悄悄收窄的 scope、证据 log 与声称结论不符。
- 专查**措辞红旗**：`should/seems/大概/基本上/应该` 这类掩饰不确定的措辞。
- 专查 **AC 逐条对账**（声明的每条 vs 实际验证的每条）；查歧义与自相矛盾。
- 专查**验证降级**：本可 `[assert]` 的项被写成 `[judge]`/`[human]` 充数；`[assert]` 命令是裸 `curl`/`echo` 这类烟雾；`[judge]` 的裁决来自实现者自己的上下文；`[human]` 缺真实签收人。
- 专查**交付面冒充**：`## 交付面` 声明的每个面是否都有真实实现与证据支撑；验证项不能跨面冒充；可断言的面不要用 human 充数（该面该什么 kind 按项目 `.claude/rules`）。
- 专查**过期声明**：Technical Framing 里的版本/最新 API 无 `查证于 <日期>` 标注；或标注日期之后该栈已发新版却未重新查证；或代码实际版本与 PRD 不符却没有变更记录。
- 专查**覆盖缺口**：AC 声称的某个维度没有任何验证项真正触及，slice 却声称整体已验证。逐 obligation 对照它的 AC 维度，确认 evidence 真绑到该 obligation（`obligation_id` 对得上）。
- 不只看 diff 本身：抽查改动点的上下游调用，确认接缝真实工作。

## 触发时机

review 在以下时机触发：

1. **软提醒**：`seed done` 成功后，PostToolUse hook 会注入提醒到上下文（`additionalContext`），建议 Claude 执行 review。
2. **用户主动触发**：用户说"review 这个 slice"或"/review"。
3. **impl 完成后**：impl SKILL 会在所有 slice 完成后建议用户触发 review（作为兜底）。

**软提醒流程**：

```text
impl 执行 slice
  ↓
[assert] seed run-check → evidence
  ↓
[judge] review 派 subagent 评分 → score-file → evidence
  ↓
seed done → 勾选 checkbox
  ↓
PostToolUse hook 检测到 seed done 成功
  ↓
hook 注入 additionalContext: "建议执行 /review 审计"
  ↓
Claude 看到提醒，决定是否执行 /review
  ↓
├─ 执行 review → 通过 → 继续下一个 slice
├─ 执行 review → 不通过 → 修复 → 重新跑 → seed done → 再次提醒
└─ 不执行 review → 继续下一个 slice（不推荐）
```

**防止重复提醒**：hook 会检查 `review.md` 是否已有 review 记录，避免重复注入提醒。

**注意**：hook 只能注入提醒，不能强制 Claude 执行 /review。是否执行取决于 Claude 的判断。

## 处理 [judge] 义务

每个 slice 的 `[assert]` 验证完成后，review 自动触发，处理该 slice 的所有 `[judge]` 义务：

1. **选择评分模式**：根据交付面价值和用户偏好，选择 Mode 1/2/3（见下文「多裁判对抗评分」）。
2. **派独立裁判**：用 `Agent` tool 派 subagent 看真实 artifact、按项目 rubric 裁决。
3. **落 evidence**：用 `seed run-check --rubric --score-file/--aggregation-file --artifact` 落盘 verdict。
4. **语义审计**：同时做 per-slice 审计（专查偷懒签名、验证降级、交付面冒充等）。

- legacy 二值 judge：使用 `--verdict pass|fail --trace ... --artifact ...`。
- scoring judge：使用 `--rubric <rubric.json> --score-file <score.json> --trace ... --artifact ...`，helper 计算 verdict；review 不手写 verdict。
- 若评分低于项目门槛，落盘 fail evidence，列入返工清单；由用户安排下一轮 impl，不自动触发。

**默认派 subagent 审计**（独立 context window，不被 impl 推理污染，生成者≠验证者）。subagent 读 PRD + diff + evidence，逐条对账，结论追加到 `review.md`。

**subagent 工具白名单**：派 subagent 时，使用 `disallowedTools: ["Edit", "NotebookEdit"]`，确保 review subagent 不能修改代码。这是硬约束，不靠 prompt 禁令。

所有审计结论必须落到 `review.md` / `evidence/`，不留口头结论。

## 多裁判对抗评分（per-slice 自动触发）

每个 slice 的 `[assert]` 验证完成后，review 自动触发，为该 slice 的 `[judge]` 义务选择评分模式。三种模式按对抗强度递增：

| 模式 | 强度 | 适用 | 实装状态 |
|---|---|---|---|
| **Mode 1: Independent Fan-out** | 低 | 多视角独立评分后聚合 | ✅ helper 已实装 |
| **Mode 2: Adversarial Fan-out** | 中 | 评分分歧大，需辩论收敛 | ✅ AI 可编排（helper 已支持聚合） |
| **Mode 3: Mechanical Classification** | 高 | 需 cross-validate 每个发现 | ✅ AI 可编排（helper 已支持聚合） |

### 设计原则（所有模式通用）

1. **物理隔离**：judge subagent 只看 artifact + rubric，**不看 impl 的推理过程**。生成者 ≠ 验证者。
2. **文件系统通信**：judge 之间通过 `scores/` 目录交换 score-file，编排者（主 session）不读 score-file 内容（避免 context 爆炸）。
3. **Judge 人格**：给 judge subagent 严格人格——默认分 3，高于 3 必须引用具体证据，低于 3 必须说明具体问题。对抗 LLM 的宽松倾向。
4. **确定性退出**：辩论最多 3 轮；共识达成或用户裁决后停止。

### 触发与模式选择

review 在每个 slice 的 `[assert]` 验证后自动触发。根据交付面价值和用户偏好选择模式：

| 场景 | 默认模式 | 用户覆盖 |
|---|---|---|
| 普通交付面（backend-domain / api / infra） | Mode 1（单裁判） | 用户明确要求"对抗审计" → Mode 2 |
| 高价值交付面（web-ui / gameplay） | Mode 1（单裁判） | 用户明确要求"多裁判评一下" → Mode 1/2/3 |
| 用户显式要求 cross-validate | Mode 3 | — |

Mode 2/3 成本高，**必须用户明确要求**才启用。

---

### Mode 1: Independent Fan-out（v1 ✅）

最简单的多裁判模式：3 个 judge 独立评分 → helper 聚合 → 落 evidence。

**流程**：

1. **Scoring phase**：Claude 用 `Agent` tool 派 3 个 subagent（如 visual-reviewer / ux-reviewer / product-reviewer），每个独立看 artifact、按 rubric 打分，输出 score-file 到 `scores/S-NNN/<reviewer>.json`。

2. **Aggregation phase**：Claude 执行 `bash` 命令 `seed score aggregate --rubric --score-files --out`，helper 计算 median，输出到 `scores/S-NNN/aggregate.json`。

3. **Evidence phase**：Claude 执行 `bash` 命令 `seed run-check --rubric --aggregation-file --trace ... --artifact`，落盘 verdict 到 `evidence/`。

**分歧处理**：如果 `aggregate.json` 中某维度 `range > 2`，review.md 记录分歧点，由用户裁决。

**示例**：

```text
用户："review 这个 slice，用多裁判评一下"

Claude 执行：
  派 3 个 subagent（Agent tool）独立评分
    → scores/S-009/visual.json
    → scores/S-009/ux.json
    → scores/S-009/product.json
  seed score aggregate --rubric ... --score-files ... --out ...
    → scores/S-009/aggregate.json
  seed run-check --aggregation-file ...
    → evidence/S-009/003-judge.json
```

---

### Mode 2: Adversarial Fan-out（✅ AI 可编排）

借鉴 [judge-with-debate](https://github.com/NeoLabHQ/context-engineering-kit) 和 [adversarial-review](https://github.com/alecnielsen/adversarial-review)：评分分歧大时进入辩论轮次。Helper 只负责聚合，辩论编排由 AI 完成。

**触发条件**：Mode 1 聚合后，`aggregate.json` 中任一维度 `range > 2`，且用户选择对抗模式。

**流程**：

1. **Scoring phase**（同 Mode 1）：3 个 judge 独立评分。

2. **Aggregation phase**（同 Mode 1）：计算 median + range。

3. **分歧检测**：检查 `aggregate.json` 的 `dimensions.<name>.range`。如果 `range > 2`，进入辩论。

4. **Debate phase**（最多 3 轮）：
   - 每个 judge subagent 读其他 judge 的 score-file（从 `scores/S-NNN/` 目录）
   - 找出自己与其他 judge 分差 > 1 的维度
   - 为自己的评分辩护（引用 artifact 中的具体证据）
   - 挑战其他 judge 的评分
   - 如果被说服，输出修订后的 score-file 到 `scores/S-NNN/<reviewer>.round-N.json`
   - **编排者不读 score-file**，只检查文件是否生成

5. **Re-aggregation**：每轮辩论后重新执行 `seed score aggregate`，检查 `range` 是否缩小。

6. **退出条件**（满足任一）：
   - 所有维度 `range ≤ 1`（共识达成）
   - 完成 3 轮辩论（强制停止）
   - 用户手动停止

7. **Evidence phase**：用最终 aggregate.json 落 evidence。

**关键**：judge 通过文件系统通信，编排者不读 score-file 内容（避免 context 爆炸）。

**示例**：

```text
用户："review 这个 slice，对抗审计"

Claude 执行：
  Mode 1 流程（Scoring + Aggregation）
    → aggregate.json: visual range=3 (judge-1=2, judge-2=5, judge-3=3)
  检测到 visual range=3 > 2，进入辩论
  Debate Round 1:
    每个 judge 读其他 judge 的 score-file，输出 .round-2.json
  Re-aggregation
    → aggregate.json: visual range=1 (共识达成)
  Evidence phase
```

---

### Mode 3: Mechanical Classification（✅ AI 可编排）

借鉴 [Adverse](https://github.com/addyosmani/adverse)：AI 按 `range` 机械分类每个维度（cross-validated / consensus / disputed / solo），不经 helper 判断。Helper 只负责聚合输出 `range` 字段。

**触发**：用户说"分类审计"或"cross-validate"。

**流程**：

1. **Scoring + Aggregation**（同 Mode 1）。

2. **Classification phase**：`seed score aggregate --classify` 输出每个维度的分类：

   | 分类 | 条件 | 含义 |
   |---|---|---|
   | `cross-validated` | 所有 judge 给分相同（range=0） | 强共识 |
   | `consensus` | range ≤ 1 | 弱共识 |
   | `disputed` | range = 2 | 有分歧 |
   | `solo` | range > 2 | 严重分歧，需辩论或用户裁决 |

3. **Output**：`review.md` 按分类展示，`solo` 和 `disputed` 维度标记为需用户裁决。

4. **Evidence phase**：用 aggregate.json 落 evidence（所有维度都落，包括 disputed）。

**示例**：

```text
用户："review 这个 slice，分类审计"

Claude 执行：
  Scoring + Aggregation
  seed score aggregate --classify
    → aggregate.json:
        visual: score=4, range=0, classification=cross-validated
        hierarchy: score=3, range=1, classification=consensus
        empty_states: score=2, range=3, classification=solo
  review.md 记录：
    ✅ cross-validated: visual=4（3 个 judge 一致）
    ✅ consensus: hierarchy=3（range=1）
    ⚠️ solo: empty_states=2（range=3，需用户裁决）
  Evidence phase
```

---

### 默认模式与成本

**默认 Mode 1**（单裁判）对大多数任务足够。Mode 2/3 成本高（3x token 起），仅在用户显式要求或高价值交付面时使用。

review 自动触发是 per-slice 的，确保每个 slice 的 judge 义务都被处理，且能即时发现问题（而非等到所有 slice 完成）。

## 输出

把结论**追加**到 `.arbor/tasks/<task>/review.md`（不覆盖历史）：

```markdown
## Review <日期> (base: <ref>)

结论：通过 | 通过但有备注 | 需要返工
<!-- 备注含非阻断性建议时选“通过但有备注”；含任何必须修复的发现选“需要返工” -->

逐条发现：
- [AC-N] <实现位置 / 证据 / 差距>
...

建议：<返工项或后续动作>
```

不改代码、不改 prd.md、不动 checkbox。需要返工时列出具体清单，由用户安排下一轮 impl。

## 结束

审计完成或返工清单列出后即停，不自动触发下一轮 impl 或 review。
