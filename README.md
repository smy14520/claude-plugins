# claude-plugins

Claude Code / OpenCode 知识管理插件集合。

## 插件列表

| 插件 | 平台 | 说明 |
|------|------|------|
| [autolearn-sdd-kit](./plugins/autolearn-sdd-kit/) | Claude Code | 完整版（设计 + 开发 + 知识管理） |
| [autolearn-sdd-kit-opencode](./plugins/autolearn-sdd-kit-opencode/) | OpenCode | 精简版（知识管理核心功能，与 Claude Code 共享数据） |

## 核心理念

**知识复利** — 每次开发都是学习，每次经验都值得沉淀。

```
开发 → 沉淀经验 → 下次开发自动检索 → 避免踩坑 → 继续沉淀
```

## 数据存储

所有知识数据存储在项目的 `.claude/` 目录下：

```
<your-project>/
├── .claude/
│   ├── experience/     # 经验文档 + INDEX.md
│   ├── modules/        # 模块索引 + INDEX.md
│   ├── rules/          # 风险规则 (risk-rules.md)
│   ├── plans/          # 设计方案
│   └── tasks/          # 任务清单
```

## 工作流

```
/design <需求>      # 架构师访谈 → 设计方案
/tasks <需求>       # 任务规划 → 任务清单
/impl <需求>        # 开发者执行 → 代码实现
/extract-experience # 沉淀经验 → 知识库
```

## 知识管理命令

| 命令 | 功能 |
|------|------|
| `/remember` | 即时记录坑点 |
| `/extract-experience` | 沉淀经验文档 |
| `/module-index` | 生成模块索引 |
| `/optimize-flow` | 沉淀风险规则 |
| `/index-rebuild` | 重建经验索引 |
| `/meta-maintain` | 检查元数据健康度 |

## Agent 自动触发

- **ContextDetective**: 开始开发前自动检索相关经验和风险提示
- **KnowledgeEngineer**: 通过命令触发，提炼经验

## 安装

### Claude Code

将插件目录软链接到项目：

```bash
# 项目级安装
ln -s /path/to/claude-plugins/plugins/autolearn-sdd-kit/.claude-plugin ~/.claude/projects/<project-path>/
```

### OpenCode

```bash
cd plugins/autolearn-sdd-kit-opencode
./install.sh
```

## 更新

```bash
cd /path/to/claude-plugins
git pull
# 自动生效
```
