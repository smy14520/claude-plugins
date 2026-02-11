---
command: /index-rebuild
description: 重建经验索引
aliases: [/index-update]
---

# /index-rebuild

维护 `.claude/context/experience/INDEX.md` 反向索引。

## 用法

```bash
/index-rebuild    # 重建完整索引
/index-update     # 增量更新
```

## 路径说明

**索引文件位于项目目录**：`.claude/context/experience/INDEX.md`

## 如何重建索引

执行完整重建：

1. **扫描所有经验文档**：遍历 `.claude/context/experience/` 目录
2. **解析元数据**：从每个文档的 frontmatter 中提取元数据
3. **构建反向索引**：按 Tag、模块、日期等维度建立索引
4. **生成 INDEX.md**：输出结构化的索引文件

## 如何增量更新

执行增量更新：

1. **识别新增文档**：对比现有索引，找出未收录的新文档
2. **更新已有文档**：检查已有文档的元数据是否有变化
3. **合并索引**：将新信息和更新合并到现有索引中
4. **保存结果**：更新 INDEX.md 文件

## 索引结构

```markdown
# 经验文档索引

## 按标签索引
- #oauth: [OAuth最佳实践.md, GitHub SSO集成.md]
- #database: [数据库连接池优化.md, 查询性能优化.md]

## 按模块索引
- Auth: [OAuth最佳实践.md, 用户认证模块.md]
- User: [用户注册流程.md, 个人信息管理.md]

## 按日期索引
- 2024-01: [OAuth最佳实践.md, 数据库连接池优化.md]
- 2024-02: [GitHub SSO集成.md]

## 文档列表
1. OAuth最佳实践.md
   - Tags: #oauth, #security
   - Module: Auth
   - Updated: 2024-01-15
   - Related: [GitHub SSO集成.md]
2. 数据库连接池优化.md
   - Tags: #database, #performance
   - Module: Common
   - Updated: 2024-01-20
   - Related: []
```

## 自动触发

自动在 `/extract-experience` 完成后触发更新。

## 使用场景

- **新建经验文档后**：自动或手动执行 `/index-update`
- **定期维护**：每周执行一次 `/index-rebuild` 确保索引完整
- **文档重组后**：移动或删除文档后重建索引
