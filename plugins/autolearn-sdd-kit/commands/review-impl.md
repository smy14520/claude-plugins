---
command: /review-impl
description: 审查实现代码的质量
---

# /review-impl

审查已完成的实现代码质量。独立于 `/impl` 流程，按需调用。

## 用法

```bash
/review-impl <需求名>
```

## 执行

1. 读取 `./.claude/tasks/<需求名>.tasks.md` 任务定义
2. 读取 `./.claude/plans/<需求名>-plan.md` 设计意图
3. **独立读取所有涉及的源文件**（不信任之前的实现报告）
4. 执行审查：
   - Spec 合规性 — 逐条验证验收标准
   - 代码质量 — 正确性、安全性、一致性、可维护性
   - 遗漏检查 — 未执行的 step、残留 TODO
5. 输出审查报告，给出 PASS / PASS WITH WARNINGS / FAIL 结论
