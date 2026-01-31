---
name: meta-maintainer
description: 经验文档元数据维护
triggers: [/meta-maintain, /meta-check]
---

# meta-maintainer

检查并更新经验文档的元数据。

## 命令

```bash
/meta-maintain              # 检查所有
/meta-maintain --auto-fix   # 自动修复
/meta-check                 # 仅检查不修复
```

## 检查项

| 检查 | 说明 | 可自动修复 |
|------|------|-----------|
| files_exist | 引用文件是否存在 | ❌ |
| updated | 日期是否准确 | ✅ |
| related | 引用文档是否存在 | ✅ |
| content_stale | 内容是否过时 | ❌ |

建议每周执行一次检查。
