---
name: tdd
description: "Test-driven development at public seams. Use when implementing features, fixing bugs test-first, writing integration or unit tests, or when mentioning 'tdd', 'test-first', 'red-green'."
---

# Test-Driven Development (TDD)

TDD 是在预定接缝（Seams）上验证公共行为的红绿循环。好的测试如同规格说明书，只通过公共接口观测行为，对内部实现重构免疫。

## 接缝规则（Seams Rule）

1. **测试只落在预定的深接缝（Pre-agreed Seams）上**：
   - 接口是接缝，内部实现是黑盒；
   - 绝不为私有函数或内部辅助类写脆弱单测；
   - 动手前必须在屏幕上写出本次测试的 Seam 签名。
2. **测试验证行为而非结构**：
   - 测“输入什么，产生什么可观测结果与状态变化”；
   - 只要契约保持，内部算法推倒重写三次，测试一行都不动。

## 循环规则（The Loop）

### Phase 1: RED（先红）
- 针对当前 Seam 编写一条最小的端到端行为测试用例；
- 运行测试并**在终端输出执行命令与变红输出**；
- **Completion criterion**：亲眼看到测试失败，且失败原因确凿是“功能未实现”（而非语法错误或配置缺失）。

### Phase 2: GREEN（变绿）
- 编写最直接、足够的生产代码使测试通过；
- 严禁在该阶段脑补未来需求或编写超出测试范围的代码；
- **Completion criterion**：运行测试并确认 exit code 为 0。

### Phase 3: REFACTOR（护盾下重构）
- 在测试全绿的安全网保护下，应用 `codebase-design` 深模块原则重构内部：
  - 提取公共逻辑、消除重复、强化错误防守；
- 随时重跑测试，确保每一步重构测试均保持绿。

## 反模式（Anti-Patterns）

- **Testing Internals**：Mock 内部函数或断言内部私有变量。只要实现一改，测试必挂。
- **Refactoring While Red**：测试还是红的时候试图优化架构。必须先以最快路径变绿。
- **Speculative Code**：编写了当前测试没有断言的额外分支或参数。
- **Brittle Fixtures**：测试过度依赖大而全的全局 Mock，导致逻辑微调引发多处测试雪崩。
