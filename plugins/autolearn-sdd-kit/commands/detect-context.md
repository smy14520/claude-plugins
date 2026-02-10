---
command: /detect-context
description: 检索任务相关上下文
agent: ContextDetective
---

# /detect-context

调用 **ContextDetective**（上下文侦探）在执行前快速加载相关知识，减少盲读代码。

## 用法

```bash
/detect-context <需求描述>
/detect-context "实现 GitHub SSO 登录"
```

## 执行

1. 调用 **ContextDetective** Agent
2. 按顺序检索：
   - `./.claude/rules/risk-rules.md`（风险规则）
   - `./.claude/experience/INDEX.md`（经验索引）
   - `./.claude/modules/`（模块索引）
3. 输出命中的风险提示、经验文档、模块索引
4. 若文件不存在，明确输出“未找到”，不中断流程

## 输出格式

```text
【ContextDetective 报告】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目: <项目名>
需求: <需求描述>

⚠️ 风险提示:
  • <风险提示1>

📄 相关经验 (N):
  • <经验文档1>

📦 模块索引 (N):
  • <模块索引1>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 完成后

```text
下一步:
- 设计阶段: /design <需求描述>
- 实现阶段: /impl <需求名>
```
