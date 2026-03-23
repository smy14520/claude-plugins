---
command: /remember
description: 即时记录 Gotcha（易错点），支持标签分类
---

# /remember

即时记录 Gotcha（易错点），不中断当前工作流。按标签自动分文件存储。

## 用法

```bash
/remember "<描述>"
/remember --tag=auth "<描述>"
/remember --tag=database,performance "<描述>"
```

## 示例

```bash
/remember "雅典娜配置有 20 种商品类型，要逐一处理"
/remember --tag=oauth "OAuth 回调必须验证 state 参数"
/remember --tag=database,connection "连接池默认值太小，需要调到 20"
```

## 执行

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

- [2026-02-11] OAuth 回调必须验证 state 参数
- [2026-03-05] refresh_token 过期后必须重新走授权流程
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
