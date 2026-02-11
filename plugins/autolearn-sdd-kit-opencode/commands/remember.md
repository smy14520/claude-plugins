---
description: 即时记录坑点（支持标签分类）
---

即时记录坑点，不中断当前工作流。支持标签分类。

## 用法

```
/remember "<坑点描述>"
/remember --tag=auth "<坑点描述>"
/remember --tag=database,performance "<坑点描述>"
```

等价于：`$ARGUMENTS` 为完整参数。

## 示例

```
/remember "雅典娜配置有 20 种商品类型，要逐一处理"
/remember --tag=oauth "OAuth 回调必须验证 state 参数"
/remember --tag=database,connection "连接池默认值太小，需要调到 20"
```

## 执行

追加到 `./.claude/experience/坑点记录.md`（与 Claude Code 共享）

### 存储格式

**有标签时**，按标签分组追加：

```markdown
#### #oauth
- [2026-02-11] OAuth 回调必须验证 state 参数

#### #database
- [2026-02-11] 连接池默认值太小，需要调到 20
```

**无标签时**，追加到 `#### #未分类` 分组：

```markdown
#### #未分类
- [2026-02-11] 雅典娜配置有 20 种商品类型，要逐一处理
```

**多标签时**，在每个标签分组下都追加一份。
