# 四态审查状态机

Review 衡量的是：**actual diff 是否在语义上满足 package PRD scope、Acceptance Criteria、Technical Framing 与 required check evidence**。Review verdict 不等于 PR approval、merge 或 release。

四态选哪个由 SKILL.md 「Verdict 决策树」按顺序判定，本文件只描述每态的语义边界与 CLI 入参。

## APPROVED

**含义**：所有 slice 完成标志已对账（实现 + 测试 / check evidence 均到位），且 `impl_result.concerns` 与你 audit 出的妥协数一致，无遗漏 concern。

CLI: `--state approved`

## APPROVED_WITH_NOTES

**含义**：语义层正确，slice 完成标志全部对账通过，但 impl 漏了 1-2 条 concern（你在 review note 里追加），或有非阻断性后续建议。

CLI: `--state approved_with_notes`

## NEEDS_REWORK

**含义**：diff 与 PRD / impl evidence 之间存在语义缺口。常见触发条件：

- 任一 slice 完成标志在 diff 中找不到对应实现；
- 任一 slice 完成标志没有对应测试断言或 check evidence（且非纯展示）；
- 任一 required_check 没有 passed evidence，或 automated check 缺 `run-check` exit_code=0；
- impl 漏了 ≥3 条 concern。

Impl 必须按 review 报告里的「缺口」列重新处理当前 package。

CLI: `--state needs_rework`

## BRAINSTORM_DRIFT

**含义**：diff 看起来合理，但 PRD 本身是错误的、失效的或与当前 repo 脱节。退回 brainstorm 更新 `prd.md`，而非 impl。

CLI: `--state brainstorm_drift`
