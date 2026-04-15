---
name: review-plan
description: 审查任务计划的质量 — 检查原子化程度、依赖关系、占位符、验收标准完整性
---

# Review Plan

审查 `.claude/tasks/<需求名>.tasks.md` 的任务计划质量。

## 触发方式

```bash
/autolearn-sdd-kit:review-plan <需求名>
```

## 审查清单

### 1. 原子化检查

先判断该任务采用的是 Strict atomic mode 还是 Lean task mode，再逐条检查。

对每个 step 逐一检查：
- [ ] 是否是一个明确的动作（不是模糊描述）
- [ ] 是否包含精确的文件路径或稳定锚点
- [ ] 简单修改是否提供足够定位信息（函数名/模块名/必要时行号）
- [ ] 新建文件或复杂逻辑是否提供足够结构信息（Strict 可给完整代码，Lean 可给关键骨架/明确约束）
- [ ] 运行命令是否有明确的预期输出

**红旗**：
- "实现 XX 功能" — 太模糊
- "添加适当的处理" — 什么叫"适当"？
- "和之前类似" — 必须写具体代码

### 2. 占位符扫描

搜索以下关键词，发现任何一个即为问题：
- TBD、TODO、FIXME、HACK、XXX
- "待定"、"待补充"、"类似"
- 空的代码块（``` ```之间没有内容）

### 3. 依赖关系验证

- [ ] `depends_on` 标注是否准确
- [ ] 是否存在循环依赖
- [ ] Shared Task 是否排在被依赖的位置
- [ ] 可并行的 Task 是否确实没有文件冲突

### 4. 验收标准检查

- [ ] 每个 Task 都有 acceptance 标准
- [ ] 标准是可验证的（能通过测试/命令/观察确认）
- [ ] 不是模糊的（"代码质量好"、"性能足够"）

### 5. 覆盖率检查

对照原始设计方案（`./.claude/plans/<需求名>-plan.md`）：
- [ ] 设计方案中的每个功能点都有对应 Task
- [ ] 没有遗漏的边界情况
- [ ] 没有遗漏的错误处理需求

## 输出格式

```markdown
## Plan Review: <需求名>

### Summary
- Total Tasks: X
- Total Steps: Y
- Issues Found: Z (Critical: A, Warning: B, Info: C)

### Issues

#### Critical (必须修复才能执行)
- [Task N, Step N.M] <问题描述> → <修复建议>

#### Warning (建议修复)
- [Task N, Step N.M] <问题描述> → <修复建议>

#### Info (可优化)
- [Task N] <建议> → <优化方向>

### Verdict
✅ PASS — 计划质量良好，可以执行 /autolearn-sdd-kit:impl
⚠️ PASS WITH WARNINGS — 可以执行，但建议先修复 Warning
❌ FAIL — 必须修复 Critical 问题后重新 /autolearn-sdd-kit:tasks
```
