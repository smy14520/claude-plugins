---
command: /design
description: 方案设计
agent: Architect
---

# /design

调用 **Architect**（架构师）进行方案设计。

## 用法

```bash
/design <需求描述>
/design   # 如果在 /req-dev 流程中，自动获取需求
```

## 执行

1. 调用 **Architect** Agent
2. Architect 设计 Spec & Plan
3. 产出 `~/.claude/context/plans/<需求名>-plan.md`
   - 文件头包含 `review_status: pending`
4. ⏸️ **暂停等待确认**

## 确认流程

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 设计方案已完成，请审阅

您可以：
- 输入 "确认" 或 "ok" → 继续下一步（/breakdown）
- 输入 "修改: <意见>" → 修改方案后重新审阅
- 输入 "重做" → 从头重新设计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

确认后：
1. 更新 `review_status: approved`
2. 继续执行 `/breakdown`
