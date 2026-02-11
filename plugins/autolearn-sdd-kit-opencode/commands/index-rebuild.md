---
description: 重建经验索引
---

维护 `.claude/experience/INDEX.md` 反向索引（与 Claude Code 共享）。

## 用法

```
/index-rebuild           # 重建完整索引
/index-rebuild update    # 增量更新
```

等价于：`$1` 为操作模式（可选，默认重建）。

## 如何重建索引

1. **扫描所有经验文档**：遍历 `.claude/experience/` 目录
2. **解析元数据**：从每个文档的 frontmatter 中提取元数据
3. **构建反向索引**：按 Tag、模块、日期等维度建立索引
4. **生成 INDEX.md**：输出结构化的索引文件

## 如何增量更新

当 `$1` 为 `update` 时：

1. **识别新增文档**：对比现有索引，找出未收录的新文档
2. **更新已有文档**：检查已有文档的元数据是否有变化
3. **合并索引**：将新信息和更新合并到现有索引中
4. **保存结果**：更新 INDEX.md 文件

## 索引结构

```markdown
# 经验文档索引

## 按标签索引
- #oauth: [OAuth最佳实践.md, GitHub SSO集成.md]
- #database: [数据库连接池优化.md]

## 按模块索引
- Auth: [OAuth最佳实践.md, 用户认证模块.md]

## 按日期索引
- 2026-02: [OAuth最佳实践.md]

## 文档列表
1. OAuth最佳实践.md
   - Tags: #oauth, #security
   - Module: Auth
   - Updated: 2026-02-11
```

## 自动触发

自动在 `/extract-experience` 完成后触发更新。
