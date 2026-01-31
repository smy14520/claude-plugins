---
command: /optimize-flow
description: 沉淀规则
agent: KnowledgeEngineer
---

# /optimize-flow

调用 **KnowledgeEngineer**（知识工程师）将经验沉淀为规则。

## 用法

```bash
/optimize-flow "<规则描述>"
```

## 示例

```bash
/optimize-flow "SSE 长连接禁止持有数据库连接"
/optimize-flow "OAuth 回调必须验证 state 参数防止 CSRF"
```

## 执行

1. 调用 **KnowledgeEngineer** Agent
2. 分析描述，提取：
   - trigger: 触发关键词
   - level: 风险等级
   - message: 提示信息
   - solution: 解决方案
3. 生成规则预览
4. 确认后追加到 `~/.claude/context/rules/risk-rules.md`

## 规则格式

```yaml
- trigger: ["SSE", "长连接", "流式"]
  level: high
  message: "SSE 长连接禁止持有数据库连接"
  solution: "使用 Redis 缓存"
```
