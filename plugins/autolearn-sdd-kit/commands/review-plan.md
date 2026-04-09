---
command: /review-plan
description: 审查任务计划的质量
---

# /review-plan

审查 `.claude/tasks/<需求名>.tasks.md` 的任务计划质量。

## 用法

```bash
/review-plan <需求名>
```

## 执行

1. 读取 `./.claude/tasks/<需求名>.tasks.md` 任务计划
2. 读取 `./.claude/plans/<需求名>-plan.md` 原始设计方案
3. 执行审查清单：
   - 原子化检查 — 每个 step 是否是可执行动作
   - 占位符扫描 — 搜索 TBD/TODO/待定等
   - 依赖关系验证 — depends_on 是否准确、无循环依赖
   - 验收标准检查 — 是否可验证
   - 覆盖率检查 — 对照设计方案是否遗漏
4. 输出审查报告，给出 PASS / PASS WITH WARNINGS / FAIL 结论
