---
command: /remember
description: 即时记录坑点
---

# /remember

即时记录坑点，不中断当前工作流。

## 用法

```bash
/remember "<坑点描述>"
```

## 示例

```bash
/remember "雅典娜配置有 20 种商品类型，要逐一处理"
/remember "Apollo 配置格式有特殊要求"
```

## 执行

追加到 `~/.claude/context/experience/<project>/坑点记录.md`

```markdown
## 2026-01-31

- 雅典娜配置有 20 种商品类型，要逐一处理
- Apollo 配置格式有特殊要求
```
