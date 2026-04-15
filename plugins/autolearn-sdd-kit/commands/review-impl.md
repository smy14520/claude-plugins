---
name: review-impl
description: 审查实现代码的质量
argument-hint: "[需求名]"
allowed-tools: "Read, Grep"
model: sonnet
---

# /autolearn-sdd-kit:review-impl

审查已完成的实现代码质量。独立于 `/impl` 流程，按需调用。

## 用法

```bash
/autolearn-sdd-kit:review-impl <需求名>
```

## 执行

这是一个纯 checker 命令，不做修复、不做二次实现、不做额外委派。

1. 读取 `./.claude/tasks/<需求名>.tasks.md` 任务定义。
2. 读取 `./.claude/plans/<需求名>-plan.md` 设计意图。
3. 只读取 tasks 中涉及的源码文件，独立验证实现结果；不要做与当前需求无关的仓库级扩展探索。
4. 执行审查：
   - Spec 合规性 — 逐条验证验收标准
   - 代码质量 — 正确性、安全性、一致性、可维护性
   - 遗漏检查 — 未执行的 step、残留 TODO
5. 直接输出审查报告与 PASS / PASS WITH WARNINGS / FAIL 结论。
