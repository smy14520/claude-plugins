---
name: index-manager
description: 经验索引管理（全局目录）
triggers: [/index-rebuild, /index-update]
---

# index-manager

维护 `~/.claude/context/experience/INDEX.md` 反向索引。

## 路径说明

**索引文件位于全局配置目录**：`~/.claude/context/experience/INDEX.md`

## 命令

```bash
/index-rebuild    # 重建完整索引
/index-update     # 增量更新
```

自动在 `/extract-experience` 完成后触发更新。
