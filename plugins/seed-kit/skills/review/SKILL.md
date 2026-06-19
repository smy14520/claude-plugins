---
name: review
description: "审计一个 seed-kit 任务的实现：读 PRD + diff + evidence，逐条 AC 对账并专查偷懒签名，结论追加到 review.md。不改代码、不改需求、无状态流转。仅用户主动触发。"
---
# Review — 语义审计

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

用干净视角审计实现是否兑现了 PRD 承诺。生成者 ≠ 验证者：不要依赖 impl 过程的叙述，只看 PRD、代码 diff 和落盘证据。

## 输入

1. `.arbor/tasks/<task>/prd.md` + `slices/S-NNN.md` —— 逐条 AC 和每个 slice 的验收。
2. 代码 diff —— base 由用户指定；未指定时从 git log 推断本任务起点并向用户确认。
3. `seed status <task> --json` + `evidence/` —— 核对每条验证的真实执行记录（命令、exit_code、输出）。

## 对账

先读项目的 `.claude/rules/`（测试纪律）与 `DESIGN.md`（品味）——按项目标准判断"该有什么验证、质量门槛够不够"；项目无则用通用地板。

- 每条 AC 映射到具体代码/测试：在哪里实现、哪条证据证明它成立，包括失败路径。
- 每个行为变更映射回 AC；多余的"顺手改进"按漂移记录。
- 专查偷懒签名：弱化或删除的断言、吞掉的异常、抄实现的假测试、新增 lint/类型抑制注释、悄悄收窄的 scope、证据 log 与声称结论不符。
- 专查**措辞红旗**：`should/seems/大概/基本上/应该` 这类掩饰不确定的措辞。
- 专查 **AC 逐条对账**（声明的每条 vs 实际验证的每条）；查歧义与自相矛盾。
- 专查**验证降级**：本可 `[assert]` 的项被写成 `[judge]`/`[human]` 充数；`[assert]` 命令是裸 `curl`/`echo` 这类烟雾（只证可达不证语义）；`[judge]` 的 verdict 来自实现者自己的 session（违反生成者≠验证者）；`[human]` 缺真实签收人。
- 专查**交付面冒充**：`## 交付面` 声明的每个面是否都有真实实现与证据支撑；验证项不能跨面冒充（声明 web-ui 却只给标 backend-domain 的后端测试）；可断言的面不要用 human 充数（该面该什么 kind 按项目 `.claude/rules`）。
- 专查**过期声明**：Technical Framing 里的版本/最新 API 无 `查证于 <日期>` 标注；或标注日期之后该栈已发新版却未重新查证；或代码实际版本与 PRD 不符却没有变更记录。
- 专查**覆盖缺口**：AC 声称的某个维度没有任何验证项真正触及（如只测正确路径漏失败路径、只测主流程漏边界），slice 却声称整体已验证——一条线通过不能冒充另一条线的覆盖。**逐 obligation 对照它的 AC 维度**：义务的可观测行为是否真覆盖了 AC 声称的维度，evidence 是否真绑到该 obligation（`obligation_id` 对得上），而不是套一个相关命令/截图就声称覆盖。这是 obligation 模式下抓"假覆盖"的核心能力。
- 不只看 diff 本身：抽查改动点的上下游调用，确认接缝真实工作。

## 作为独立裁判（judge）

judge 由独立 agent 做（生成者≠验证者）。两条路径：
- **per-slice judge**：impl 跑绿 assert 后派 reviewer subagent 裁（见 impl SKILL），review 不参与。
- **整体审计时**：review 触发后按下方「选模式」执行；若发现 impl 漏裁的 `[judge]`，review 兜底裁决：看真实产物、按 rubric，用 `seed run-check` 落盘 verdict（完整命令见 conventions）。judge 调用必带 `--verdict pass|fail` 与 `--artifact`。verdict=fail 记返工清单。

### 体验质量类 judge：评分循环

不做二值判定，走"看真实产物 → 按项目 rubric 各维度打分 + critique → 不到 bar 记返工 → impl 改 → 再看再裁"的循环，直至通过。落盘用 `--grade`（各维度分）+ `--trace`（依据 + 不到 bar 的点）+ `--artifact`（看过的截图）。rubric 的维度、bar、参考来自项目（`DESIGN.md` / `.claude/rules/`），插件不硬编码；rubric 压在整体设计质量与原创性、压低"通用 AI 味"，不是功能清单。grade 不进 gate（gate 只看 verdict），留给质量看板/复核。

## 输出

把结论**追加**到 `.arbor/tasks/<task>/review.md`（不覆盖历史）：

```markdown
## Review <日期> (base: <ref>)

结论：通过 | 通过但有备注 | 需要返工
<!-- 备注含非阻断性建议时选"通过但有备注"；含任何必须修复的发现选"需要返工" -->

逐条发现：
- [AC-N] <实现位置 / 证据 / 差距>
...

建议：<返工项或后续动作>
```

不改代码、不改 prd.md、不动 checkbox。需要返工时列出具体清单，由用户安排下一轮 impl。

## 结束

审计完成或返工清单列出后即停，不自动触发下一轮 impl 或 review。

## 选模式（整体审计怎么执行）

整体审计按任务特征选执行模式。三种 review worker 都用 `seed run-check` 落盘（统一契约，完整命令见 conventions），区别只在编排：

| 任务特征 | 模式 | 编排 |
|---|---|---|
| 默认 / 单视角逐条对账 | **subagent** | 派 `Agent`（独立 context）逐条对账 |
| 多个不重叠 lens（安全+性能+体验）**且要互相证伪** | **agent team** | `TeamCreate` 开 reviewer teammate，peer 互相挑战，配 `TaskCompleted` hook（exit 2 阻断 task 完成）做门控 |
| judge **多角度独立评分后聚合** / 多 slice / codebase-wide sweep | **workflow** | `Workflow` 脚本 fan-out 多裁判，投票/filter 聚合 |

**启动 team/workflow 前需用户同意**：给一句话理由 + 推荐（如"本任务有 3 个对抗 lens，建议开 team"），subagent 全自动。team/workflow token 重，符合"AI recommends, user decides"，默认不静默启动。
