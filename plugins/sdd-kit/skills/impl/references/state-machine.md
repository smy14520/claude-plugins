# Impl states

Impl 对单个 package PRD scope 只报告四种结果。Package 顶层 lifecycle 只有 `draft → ready → doing → done → reviewed`；DONE 不等于 merged 或 delivered。

每个 slice 有对应的 `slices/S-NNN.md` task 文件，包含 Acceptance（G/W/T 硬约束）、Approach（推荐路径）、Verification（验证命令）。Impl 以 task 文件的 Verification 通过 + Acceptance Then 满足为 done 标准。

## DONE

当前 package PRD scope self-check 通过，无已知妥协。必须记录检查依据和命令结果。

## DONE_WITH_CONCERNS

A/B 通过且**功能代码兑现 PRD 承诺**，仅 C 因非阻塞环境限制无法完整验证。完整判定见 SKILL.md verdict 表。

每条 concern 必须写 "PRD 完成标志原意 vs 实际实现"。若功能未兑现 PRD（典型如用替代方案顶替承重决策），不是 concern，应报 NEEDS_CONTEXT 或 BLOCKED。

## NEEDS_CONTEXT

继续执行会变成猜测。常见原因：

- PRD scope / acceptance 太薄。
- Technical Framing 缺少承重决定。
- Slices 与目标 / 验收冲突或缺关键步骤。
- 缺少影响行为的具体选择。

输出时说明：受阻点、需要的问题、歧义来源、当前代码状态。

## BLOCKED

环境 / 外部因素让 impl **无法完成实现**或**无法判断核心功能是否工作**。常见：依赖装不上、权限 / 认证缺失、外部服务不可达、关键 parser 因系统库缺失无法运行。

对照 DONE_WITH_CONCERNS：功能完整、只是验证手段受限不是 BLOCKED，见 SKILL.md verdict 表。
