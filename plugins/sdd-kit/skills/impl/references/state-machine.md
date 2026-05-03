# Impl states

Impl 对单个 package PRD scope 只报告四种结果。Package 顶层 lifecycle 只有 `draft → ready → doing → done → reviewed`；DONE 不等于 merged 或 delivered。

## DONE

当前 package PRD scope self-check 通过，无已知妥协。必须记录检查依据和命令结果。

## DONE_WITH_CONCERNS

self-check 通过，但实现有需要 review 知道的顾虑或妥协。

## NEEDS_CONTEXT

继续执行会变成猜测。常见原因：

- PRD scope / acceptance 太薄。
- Technical Framing 缺少承重决定。
- Slices 与目标 / 验收冲突或缺关键步骤。
- 缺少影响行为的具体选择。

输出时说明：受阻点、需要的问题、歧义来源、当前代码状态。

## BLOCKED

环境或外部因素阻止执行，例如依赖、权限、认证、服务不可达或外部系统不可用。
