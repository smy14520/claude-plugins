---
name: optimize-flow
description: 沉淀规则
argument-hint: "[规则描述]"
allowed-tools: "Read, Write, Edit, Task"
model: sonnet
---

# /autolearn-sdd-kit:optimize-flow

调用 **KnowledgeEngineer**（知识工程师）将经验沉淀为风险规则。

## 用法

```bash
/autolearn-sdd-kit:optimize-flow "<规则描述>"
```

## 示例

```bash
/autolearn-sdd-kit:optimize-flow "SSE 长连接禁止持有数据库连接"
/autolearn-sdd-kit:optimize-flow "OAuth 回调必须验证 state 参数防止 CSRF"
```

## 执行

这是一个薄 orchestrator 命令：
- 输入明确时直接处理，不做闲聊式反问
- 只委派一次给 `KnowledgeEngineer`
- 结果可落盘时立即写入 `./.claude/rules/risk-rules.md`
- 不输出“如果你愿意我下一步可以……”这类聊天式尾句

1. 调用 **KnowledgeEngineer** Agent
2. 分析描述，提取关键信息
3. 生成规则内容
4. 结果可落盘时立即追加到 `./.claude/rules/risk-rules.md`

## 规则格式

每条规则是一个 Markdown 段落，包含触发关键词、风险等级、说明和解决方案：

```markdown
### ⚠️ SSE 长连接禁止持有数据库连接
**关键词**: SSE, 长连接, 流式
**等级**: 🔴 高风险

SSE/WebSocket 等长连接场景中，如果直接持有数据库连接，会导致连接池耗尽。

**解决方案**: 查询完立即释放连接，长时间数据推送使用 Redis 缓存中转。

---

### ⚠️ OAuth 回调必须验证 state 参数
**关键词**: OAuth, 回调, state, CSRF
**等级**: 🔴 高风险

不验证 state 参数会导致 CSRF 攻击，攻击者可以用自己的授权码绑定受害者账号。

**解决方案**: 生成随机 state 存入 session，回调时对比验证。
```
