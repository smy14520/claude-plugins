---
name: review-impl
description: 审查实现代码的质量 — 检查 spec 合规性、代码质量、遗漏项
---

# Review Implementation

审查已完成的实现代码质量。独立于 `/impl` 流程，用户需要时手动调用。

## 触发方式

```bash
/autolearn-sdd-kit:review-impl <需求名>
```

## 审查流程

### Step 1: 读取上下文

1. 读取 `./.claude/tasks/<需求名>.tasks.md` — 了解任务定义
   - 把原 Task 正文、acceptance、depends_on 当作 spec
   - 如果文件底部存在 `## Implementation Record` / `autolearn:impl-status` generated section，只把它当执行上下文，不要把它当规范正文
2. 读取 `./.claude/plans/<需求名>-plan.md` — 了解设计意图
3. 读取所有涉及的源文件 — 独立验证实际代码

### Step 2: Spec 合规审查

逐条检查每个 Task 的验收标准：

```markdown
## Spec Compliance

### Task 1: <名称>
- [ ] 验收标准 1: <检查结果>
- [ ] 验收标准 2: <检查结果>
...
```

**关键原则：不要信任之前的实现报告，独立阅读代码验证。**

### Step 3: 代码质量审查

检查以下维度：

| 维度 | 检查项 |
|------|--------|
| 正确性 | 逻辑是否正确，边界情况是否处理 |
| 安全性 | 输入验证、敏感数据处理、注入防护 |
| 一致性 | 代码风格是否与项目一致，命名是否规范 |
| 可维护性 | 是否有过长函数、重复代码、过度抽象 |
| 错误处理 | 异步错误是否捕获、错误信息是否有意义 |
| 类型安全 | TypeScript 类型是否完整，有无 any |

### Step 4: 遗漏检查

- [ ] 所有 step 是否都已执行（对照 tasks 文件）
- [ ] 是否有被遗漏的边界情况
- [ ] 是否有 TODO/FIXME 残留在代码中
- [ ] 是否有被注释掉的代码块

## 反偷懒约束

```
审查时如果你发现自己想说以下任何一句话，请停下来实际检查：

- "看起来应该没问题" → 去读代码
- "这个函数逻辑简单，不需要仔细看" → 仔细看
- "测试都通过了，代码应该是对的" → 读代码验证
- "变量名能说明意图" → 确认它确实准确

铁律：READ THE ACTUAL CODE. TRUST NOTHING BUT THE CODE.
```

## 输出格式

```markdown
## Implementation Review: <需求名>

### Summary
- Tasks Reviewed: X
- Spec Compliance: Y/X passed
- Issues Found: Z (Critical: A, Warning: B, Info: C)

### Spec Compliance
| Task | Status | Notes |
|------|--------|-------|
| Task 1 | ✅ PASS | All acceptance criteria met |
| Task 2 | ⚠️ PARTIAL | Missing error handling for X |
| Task 3 | ✅ PASS | — |

### Code Quality Issues

#### Critical (必须修复)
- [文件:行号] <问题描述> → <修复建议>

#### Warning (建议修复)
- [文件:行号] <问题描述> → <修复建议>

#### Info (可优化)
- [文件:行号] <建议>

### Highlight
**做得好的地方**：
- <值得肯定的设计/实现决策>

### Verdict
✅ PASS — 实现质量良好
⚠️ PASS WITH WARNINGS — 建议修复 Warning
❌ FAIL — 存在 Critical 问题，必须修复
```
