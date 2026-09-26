---
name: tdd
description: "测试驱动开发（TDD）红绿循环。适用于先写测试构建功能、修复缺陷、或需要高质量集成与行为测试时调用。"
---

# Test-Driven Development (TDD)

TDD 是 Red -> Green 循环。这个技能是让该循环产出真正值得保留的高价值测试的准绳：什么是好测试、测试应该放在哪里、三大经典反模式，以及红绿循环的规则。每个循环前后都要随时对照。

## 什么是好测试（What a good test is）

通过公共接口（Public Interfaces）验证可观测行为（Behavior）。内部代码推倒重构三次，测试一行都不该变。好测试读起来像规格说明书：`"user can checkout with valid cart"` 清楚说明了系统能力；它不关心内部函数调用结构，能承受重构。

- 完整对比示例见 [tests.md](tests.md)
- Mocking 纪律见 [mocking.md](mocking.md)

---

## Seams 规则（Where tests go）

**Seam（可观测行为边界）** 是你测试的公共契约边界。测试只落在 Seam 上。

**只测试预先认可的 Seams（Pre-agreed Seams）**：
- 写测试前先列出要测的 Seams，并请用户确认；
- 提前锁定 Seam，把有限的测试精力集中在核心关键路径和复杂业务上，而不是为每个局部 edge case 机械涂抹测试。

当接口形状本身就是问题所在时（模块该多深、Seam 应该放在哪），调用 `codebase-design` 获取标准词汇与标尺。

---

## 三大破坏性反模式（Anti-Patterns）

- **Implementation-coupled（与实现细节耦合）**：Mock 内部协作者、测试私有方法、或通过绕过接口的旁路（如直接查数据库）验证。特征是代码重构但行为没变时，测试大面积变红崩溃。
- **Tautological test（自我印证假测试）**：断言以与被测代码完全相同的方式重新计算期望值（例如被测代码写 `a + b`，测试里也用 `a + b` 算预期；或把常量断言等于它自己），因此天然全绿，永远测不出错。**期望值必须来自独立的外部真相源（Known-good Literal、Worked Example 或明确规格）**。
- **Horizontal slicing（水平切片）**：先把所有测试全写完，再去写所有实现。批量测试验证的是“想象中的行为”——测试的是形状而不是真实能力，在理解实现细节前就过早锁死了测试结构。改用 **Vertical slices（垂直切片）**：一个测试 -> 一个实现 -> 重复，每个测试都是回应上一轮认知的新 **Tracer bullet**。

---

## 循环法则（Rules of the loop）

- **Red before green（先红后绿）**：先写失败测试，亲眼看到它在该行为上失败；然后只写刚好足够让它变绿的代码。
- **One slice at a time（单一切片）**：每个循环只处理一个 Seam 行为、一个测试、一个最小实现。
- **Refactoring is not part of the loop（重构不属于本循环）**：重构属于独立审查阶段（见 `tinder-kit:code-review` 技能）。
