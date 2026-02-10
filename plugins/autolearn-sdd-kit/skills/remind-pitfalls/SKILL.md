---
name: remind-pitfalls
description: 坑点提醒（规则优先+经验提取）
triggers: [/remind-pitfalls]
input: [requirement: string]
output: [pitfalls: array]
---

# remind-pitfalls

从规则和经验文档中提取坑点并提醒。

## 执行流程

1. **规则匹配** → `./.claude/rules/risk-rules.md`（优先，0 token）
2. **经验提取** → 已加载的经验文档（兜底）
3. **去重合并** → 按严重程度排序

## 输出格式

```
⚠️ [高] SSE 长连接禁止持有数据库连接
   解决方案: 使用 Redis 缓存替代

ℹ️ [中] 注意钱包类型匹配
   解决方案: 检查 goods_type 与 wallet_type
```
