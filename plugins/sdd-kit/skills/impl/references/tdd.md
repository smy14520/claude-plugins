# TDD mode

TDD 是 impl 的执行模式，不是独立 workflow stage。只在用户明确要求 TDD，或当前 T-xxx 的主要风险是行为正确性时使用。

## Loop

1. 从当前 T-xxx 选择一个最小 observable behavior。
2. 写一个会失败的测试或验证脚本，先证明缺口存在。
3. 写最小实现让它通过。
4. 绿灯后再 refactor；不要在 red 状态重构。
5. 把测试命令、结果和关键取舍记录到 impl context。

## UI behavior

- 测用户可观察行为，不测像素和内部实现细节。
- 优先覆盖点击、输入、状态切换、错误提示、权限可见性、路由变化和 API 触发。
- component / integration / e2e 的选择取决于验收风险；不要为了 TDD 强行上最重层级。
- 视觉、动画、拖拽手感和响应式细节需要浏览器验证或 visual regression 补足。

## External boundaries

- 只在系统边界 fake / mock：第三方 API、支付、邮件、LLM、外部 webhook、时间、随机数、网络。
- 不 mock 内部业务逻辑来制造通过。
- provider adapter 用 fake server、sandbox 或 recorded fixture 验证 request/response mapping、错误码、timeout、重试和 malformed response。
- 涉及状态迁移、幂等、并发或交易语义时，优先写 integration-style behavior test。

## When not to force TDD

不要为了形式强行 TDD：纯视觉 polish、探索性 spike、一次性脚本、测试 harness 成本明显高于风险的改动，可以改用明确的 SelfCheck / browser verification。