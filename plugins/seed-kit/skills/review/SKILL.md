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

先读项目的 `.claude/rules/`（测试纪律）与 `DESIGN.md`（品味）——按项目标准判断“该有什么验证、质量门槛够不够”；项目无则按 PRD 的质量基线与通用可交付地板判断。

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

## 作为独立裁判（judge）

当任务有未裁决的 `[judge]` obligation，review 可以作为独立裁判兜底：看真实产物、按项目 rubric/PRD 质量基线裁决，并用 `seed run-check` 落盘（完整命令见 conventions）。

- legacy 二值 judge：使用 `--verdict pass|fail --trace ... --artifact ...`。
- scoring judge：使用 `--rubric <rubric.json> --score-file <score.json> --trace ... --artifact ...`，helper 计算 verdict；review 不手写 verdict。
- 若评分低于项目门槛，落盘 fail evidence，列入返工清单；由用户安排下一轮 impl，不自动触发。

默认在当前 review session 直接审计。需要隔离高噪音上下文或并行局部审查时，可派 subagent；Agent Team / Workflow 仅在用户明确要求多视角协作或大规模 fan-out 时作为外部编排使用，且最终仍必须落到 `review.md` / `evidence/`。

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
