# TDD mode

TDD 是 impl 的执行模式，不是独立 workflow stage。只在用户明确要求 TDD，或当前 package PRD scope 的主要风险是行为正确性时使用。

## Loop

1. 从当前 package PRD scope 选择一个最小 observable behavior。
2. 写一个会失败的测试或验证脚本，先证明缺口存在。
3. 写最小实现让它通过。
4. 绿灯后再 refactor；不要在 red 状态重构。
5. 按 `red signal → change → green command/result` 记录证据；最终仍要满足 PRD acceptance，并用 `record-impl-result` 记录结果。

## Interaction / observable behavior

- 测用户或系统可观察行为，不测内部实现细节。
- 覆盖 PRD 中承重交互、状态变化、错误反馈和边界行为；具体形式由项目类型决定。
- 测试层级取决于验收风险；不要为了 TDD 强行上最重层级。
- 难以用单元测试表达的体验、时序、设备或运行时细节，需要用合适的功能验证补足；TDD 通过不替代 golden path。

## External boundaries

- 只在系统边界 fake / mock：超出当前业务逻辑的外部依赖、时间、随机数、网络、设备或运行时环境。
- 不 mock 内部业务逻辑来制造通过。
- 涉及状态迁移、幂等、并发、交易语义或版本兼容时，优先写 integration-style behavior test。

## When not to force TDD

不要为了形式强行 TDD：纯视觉 polish、探索性 spike、一次性脚本、测试 harness 成本明显高于风险的改动，可以改用明确的 SelfCheck / browser verification。