---
name: index-rebuild
description: 重建经验索引
argument-hint: "[--update]"
allowed-tools: "Read, Write, Edit, Glob"
model: haiku
---

# /autolearn-sdd-kit:index-rebuild

维护 `.claude/experience/INDEX.md` 反向索引。

## 用法

```bash
/autolearn-sdd-kit:index-rebuild             # 重建完整索引
/autolearn-sdd-kit:index-rebuild --update    # 增量更新
```

## 路径说明

**索引文件位于项目目录**：`.claude/experience/INDEX.md`

## 如何重建索引

这是一个纯维护命令，不做闲聊式澄清，不做额外委派。
如果命令已经被明确触发，直接执行索引维护，不要停在命令说明或菜单式输出上。

执行完整重建：

1. **扫描所有经验文档**：遍历 `.claude/experience/` 目录
2. **解析元数据**：从每个文档的 frontmatter 中提取元数据
3. **构建反向索引**：按 Tag、模块、日期等维度建立索引，并保留紧凑的检索摘要
4. **生成 INDEX.md**：输出结构化的索引文件，优先服务定位与候选过滤

## 如何增量更新

执行增量更新：

1. **识别新增文档**：对比现有索引，找出未收录的新文档
2. **更新已有文档**：检查已有文档的元数据是否有变化
3. **合并索引**：将新信息和更新合并到现有索引中
4. **保存结果**：更新 INDEX.md 文件

## 索引结构

> ⚠️ `INDEX.md` 是纯索引文件，目标是“查找 → 定位 → 候选过滤”，不要重复正文内容。

```markdown
# 经验文档索引

| 名称 | 标签 | 关键文件 | 类型 | 更新日期 | 摘要 |
|------|------|---------|------|----------|------|
| [OAuth最佳实践.md](./OAuth最佳实践.md) | `oauth`, `security` | `src/auth/**` | `pattern` | 2024-01-15 | 处理 OAuth 接入时优先检查 state、token 生命周期与回调链路一致性 |
| [数据库连接池优化.md](./数据库连接池优化.md) | `database`, `performance` | `src/db/**` | `checklist` | 2024-01-20 | 调整连接池或长连接逻辑时先检查池大小、释放时机和超时配置 |
```

**INDEX.md 规则**：
- ✅ 保留紧凑表格，优先服务检索和候选过滤
- ✅ 摘要只写一句话，用于快速判断是否值得继续读取正文
- ❌ 不要把通用流程、坑点展开、代码示例塞进 INDEX
- 📌 更详细的场景判断放在文档 frontmatter 和正文中

## 自动触发

通常在 `/autolearn-sdd-kit:extract-experience` 完成后自动更新；手动执行主要用于批量编辑、索引修复或文档迁移后重建一致性。

## 使用场景

- **新建经验文档后**：自动或手动执行 `/autolearn-sdd-kit:index-rebuild --update`
- **定期维护**：每周执行一次 `/autolearn-sdd-kit:index-rebuild` 确保索引完整
- **文档重组后**：移动或删除文档后重建索引
