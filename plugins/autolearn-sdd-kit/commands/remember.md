---
name: remember
description: 即时记录 Gotcha（易错点），支持标签分类
argument-hint: "[描述] [--tag=标签]"
allowed-tools: "Read, Write, Edit"
model: haiku
---

# /autolearn-sdd-kit:remember

即时记录 Gotcha（易错点），不中断当前工作流。按标签自动分文件存储，保持短小、可检索、可复用。

## 用法

```bash
/autolearn-sdd-kit:remember "<描述>"
/autolearn-sdd-kit:remember --tag=auth "<描述>"
/autolearn-sdd-kit:remember --tag=database,performance "<描述>"
```

## 示例

```bash
/autolearn-sdd-kit:remember "雅典娜配置有 20 种商品类型，要逐一处理"
/autolearn-sdd-kit:remember --tag=oauth "OAuth 回调必须验证 state 参数"
/autolearn-sdd-kit:remember --tag=database,connection "连接池默认值太小，需要调到 20"
```

## 执行

这是一个超轻量记录命令：
- 不做闲聊式澄清
- 不做额外委派
- 不做多轮分析
- 输入已明确时直接写入 gotcha 与索引

外层命令的职责只有两件事：
1. 解析输入中的 tag 与 gotcha 文本
2. 直接落盘到对应 gotcha 文件和 INDEX.md

如果输入足够明确，禁止输出任何澄清、闲聊、建议下一步或备选菜单；直接执行写入并仅输出写入结果。

### 记录规则（保持轻量）

- 每条 gotcha 只记录一个坑点
- 优先写成“问题/触发条件/必须动作”这样的短句
- 避免写成过程日志、情绪描述或模糊提醒
- tag 使用稳定关键词；无把握时宁可少打，不要发散
- 如果输入已经足够明确，直接落盘，不要反问

### 动作 1：写入对应标签文件

存储目录：`./.claude/experience/gotchas/`

**按标签分文件**：
- `--tag=oauth` → 写入 `gotchas/oauth.md`
- `--tag=database` → 写入 `gotchas/database.md`
- 无标签 → 写入 `gotchas/general.md`
- 多标签 → 每个标签文件各写一份

**单个文件格式**：

```markdown
# Gotchas: oauth

- [2026-02-11] OAuth 回调缺少 state 校验会导致绑定风险；处理回调前必须先验证 state
- [2026-03-05] refresh_token 过期后会导致静默刷新失败；失效后必须重新走授权流程
```

**文件不存在时**自动创建，**已存在时**在末尾追加一行。

### 动作 2：更新 INDEX.md

更新 `./.claude/experience/gotchas/INDEX.md`：

- **文件不存在** → 创建
- **该标签行已存在** → 更新条目数和日期
- **该标签行不存在** → 追加一行

```markdown
# Gotchas 索引

| 标签 | 文件 | 条目数 | 最后更新 |
|------|------|--------|----------|
| oauth | [oauth.md](./oauth.md) | 2 | 2026-03-05 |
| database | [database.md](./database.md) | 3 | 2026-02-15 |
| general | [general.md](./general.md) | 1 | 2026-02-09 |
```
