# Impl 结果语义

Package 顶层 lifecycle 是 `draft → ready → doing → done → reviewed`（任意状态可 archived）；impl 的四种结果是记录，不是顶层状态。DONE 不等于 merged 或 delivered。

## DONE

当前 PRD scope 的全部 slice 经 mark-slice gate 结算，Functional 验证通过，无已知妥协。

## DONE_WITH_CONCERNS

功能代码兑现 PRD 承诺，仅部分验证因非阻塞环境限制无法完整执行。每条 concern 必须写 "PRD 完成标志原意 vs 实际实现"。

## NEEDS_CONTEXT

继续执行会变成猜测。常见原因：PRD scope / acceptance 太薄；Technical Framing 缺承重决定；Slices 与目标 / 验收冲突；缺少影响行为的具体选择。输出时说明受阻点、需要的问题、歧义来源、当前代码状态。

## BLOCKED

环境 / 外部因素让 impl 无法完成实现或无法判断核心功能是否工作（依赖装不上、权限 / 认证缺失、外部服务不可达等）。对照 DONE_WITH_CONCERNS：功能完整、只是验证手段受限不是 BLOCKED。
