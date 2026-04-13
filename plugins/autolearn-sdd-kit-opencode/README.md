# autolearn-sdd-kit-opencode

**OpenCode 知识套件** — 将 [autolearn-sdd-kit](../autolearn-sdd-kit/) 的知识管理能力带到 OpenCode。

> 与 Claude Code 版本**共享同一套知识数据**（`.claude/` 目录），无论用哪个工具沉淀的经验，另一个都能读取。

## 包含内容

### Agents（2 个 subagent）

| Agent | 功能 | 触发方式 |
|-------|------|----------|
| `context-detective` | 从知识库按需精准检索相关经验和风险提示 | 用户显式调用 `@context-detective` |
| `knowledge-engineer` | 从开发实践中提炼经验和规则 | 通过命令触发 |

### Commands（6 个命令）

| 命令 | 功能 |
|------|------|
| `/extract-experience` | 沉淀经验 → `.claude/experience/` |
| `/module-index` | 模块索引 → `.claude/modules/` |
| `/remember` | 即时记录坑点（支持标签） |
| `/optimize-flow` | 沉淀规则 → `.claude/rules/` |
| `/index-rebuild` | 重建/更新经验索引 |
| `/meta-maintain` | 检查经验文档元数据健康度 |

## 安装

### 全局安装（推荐）

```bash
cd plugins/autolearn-sdd-kit-opencode
chmod +x install.sh
./install.sh
```

文件通过 **symlink** 链接到 `~/.config/opencode/`，所有项目生效。

### 项目级安装

```bash
./install.sh --project /path/to/your-project
```

### 卸载

```bash
./install.sh --uninstall
```

## 更新

因为使用了 symlink，更新非常简单：

```bash
cd /path/to/claude-plugins
git pull
# 自动生效，无需其他操作
```

如果新增了文件（新的 agent 或 command），重新执行：

```bash
cd plugins/autolearn-sdd-kit-opencode
./install.sh
```

## 数据共享

所有知识数据存储在项目的 `.claude/` 目录下：

```
<your-project>/
├── .claude/                    # 共享知识数据
│   ├── experience/             # 经验文档 + INDEX.md
│   ├── modules/                # 模块索引 + INDEX.md
│   └── rules/                  # 风险规则
├── .opencode/                  # OpenCode 配置（安装后自动创建）
│   ├── agents/ → symlink
│   └── commands/ → symlink
└── ...
```

无论使用 Claude Code 还是 OpenCode 执行 `/extract-experience`、`/module-index` 等命令，数据都写入 `.claude/`，双方均可读取。

## 使用示例

```
# 在 OpenCode TUI 中

# 手动检索上下文
@context-detective 帮我检索跟用户认证相关的经验

# 沉淀经验
/extract-experience OAuth集成

# 生成模块索引
/module-index src/auth

# 记录坑点
/remember --tag=auth "Token 必须存在 httpOnly cookie 中"

# 沉淀规则
/optimize-flow "OAuth 回调必须验证 state 参数"
```
