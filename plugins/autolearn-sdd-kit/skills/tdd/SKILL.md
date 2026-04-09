---
name: tdd
description: 测试驱动开发 — 当用户要求 TDD 或项目配置了 TDD 模式时使用
---

# Test-Driven Development (TDD)

## 何时使用

**适用**：
- 用户明确要求 TDD
- CLAUDE.md 中配置了 TDD 模式
- 用户说"先写测试"、"用 TDD"

**不适用**（用户指令优先）：
- 用户说"不写测试"、"跳过测试"
- CLAUDE.md 中禁用了 TDD
- 项目没有测试框架

## 核心循环：Red → Green → Refactor

```
RED: 写一个失败的测试
  ↓
运行测试，确认它失败（且失败原因正确）
  ↓
GREEN: 写最少的代码让测试通过
  ↓
运行测试，确认全部通过
  ↓
REFACTOR: 清理代码（保持测试通过）
  ↓
重复
```

## Red — 写失败测试

```typescript
// Good: 测试真实行为，一个测试一件事
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };
  const result = await retryOperation(operation);
  expect(result).toBe('success');
  expect(attempts).toBe(3);
});

// Bad: 测试 mock 而不是真实代码
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(2); // 测的是 mock 不是逻辑
});
```

**必须运行测试确认它失败**。如果测试直接通过了，说明你在测已有行为，不是新功能。

## Green — 写最少代码

只写让测试通过的最少代码。不要加额外功能、不要提前重构。

## Refactor — 清理

测试全部通过后才能重构。重构时持续运行测试确保不破坏。

## 铁律

```
没有失败测试 → 不写生产代码
先写了生产代码 → 删掉，从测试开始
```

## 常见借口（别信）

| 借口 | 真相 |
|------|------|
| "太简单不用测" | 简单代码也会出 bug，测试只要 30 秒 |
| "先写代码再补测试" | 后补的测试只会验证你写的代码，不会验证需求 |
| "我手动测过了" | 手动测试不可重复、不可追溯 |
| "TDD 太慢" | 调试比写测试慢得多 |
| "这个项目没测试" | 你来加 |

## 验证清单

完成前逐项检查：

- [ ] 每个新函数/方法都有测试
- [ ] 每个测试都先看过它失败
- [ ] 每个测试失败的原因是"功能未实现"（不是语法错误）
- [ ] 写了最少的代码让测试通过
- [ ] 所有测试通过，输出无错误无警告
- [ ] 测试用的是真实代码（mock 只在不可避免时使用）
- [ ] 边界情况和错误情况有覆盖
