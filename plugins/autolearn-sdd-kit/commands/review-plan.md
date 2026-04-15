---
name: review-plan
description: 审查任务计划的质量
argument-hint: "[需求名]"
allowed-tools: "Read, Grep"
model: sonnet
---

# /autolearn-sdd-kit:review-plan

审查 `.claude/tasks/<需求名>.tasks.md` 的任务计划质量。

## 用法

```bash
/autolearn-sdd-kit:review-plan <需求名>
```

## 执行

这是一个纯 checker 命令，不做实现、不做二次规划、不做额外委派。

1. 读取 `./.claude/tasks/<需求名>.tasks.md` 任务计划。
2. 读取 `./.claude/plans/<需求名>-plan.md` 原始设计方案。
3. 只执行审查清单：
   - 原子化检查 — 每个 step 是否是可执行动作
   - 占位符扫描 — 搜索 TBD/TODO/待定等
   - 依赖关系验证 — depends_on 是否准确、无循环依赖
   - 验收标准检查 — 是否可验证
   - 覆盖率检查 — 对照设计方案是否遗漏
4. 直接输出审查报告与 PASS / PASS WITH WARNINGS / FAIL 结论；不要做额外探索，除非某条 issue 必须读取被点名文件才能确认。
