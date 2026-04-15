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

其中 `.claude/tasks/<需求名>.tasks.md` 现在承担两层信息：
- **Task spec**：原始任务定义、依赖、步骤、验收标准，供 `/review-plan` / `/review-impl` 读取
- **generated execution snapshot**：由 `/autolearn-sdd-kit:impl` 维护的固定状态区块，用于跨会话查看执行进度

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

> 经过真实交互会话验证，**推荐使用 namespaced 命令**。

```bash
/autolearn-sdd-kit:design <需求>      # 架构师访谈 → 设计方案
/autolearn-sdd-kit:tasks <需求>       # 任务规划 → 任务清单
/autolearn-sdd-kit:impl <需求>        # 开发者执行 → 代码实现
/autolearn-sdd-kit:impl <需求> --parallel  # 请求安全的 best-effort 并行执行
/autolearn-sdd-kit:extract-experience # 沉淀经验 → 知识库
```

## 知识管理命令

| 命令 | 功能 |
|------|------|
| `/autolearn-sdd-kit:remember` | 即时记录坑点 |
| `/autolearn-sdd-kit:extract-experience` | 沉淀经验文档 |
| `/autolearn-sdd-kit:module-index` | 生成模块索引 |
| `/autolearn-sdd-kit:optimize-flow` | 沉淀风险规则 |
| `/autolearn-sdd-kit:index-rebuild` | 重建经验索引 |
| `/autolearn-sdd-kit:meta-maintainer` | 检查元数据健康度 |

## Agent 使用方式

- **ContextDetective**: 在用户明确要求检索上下文，或任务确实需要知识库/风险规则辅助时使用
- **KnowledgeEngineer**: 通过命令触发，提炼经验

## 安装

### Claude Code

有两种可用方式：

#### 方式 A：本地开发 / 验证（推荐）

直接通过 `--plugin-dir` 加载插件根目录：

```bash
ccm --plugin-dir /path/to/claude-plugins/plugins/autolearn-sdd-kit
# 或
claude --plugin-dir /path/to/claude-plugins/plugins/autolearn-sdd-kit
```

> 注意：这里要指向 **插件根目录**（即包含 `.claude-plugin/plugin.json` 的目录），
> 不是只指向 `.claude-plugin/` 子目录。

#### 方式 B：项目级安装

将插件目录软链接到项目：

```bash
ln -s /path/to/claude-plugins/plugins/autolearn-sdd-kit/.claude-plugin ~/.claude/projects/<project-path>/
```

### 实际调用方式

在真实会话里，推荐使用 **namespaced 命令**：

```bash
/autolearn-sdd-kit:design <需求>
/autolearn-sdd-kit:tasks <需求>
/autolearn-sdd-kit:impl <需求>
/autolearn-sdd-kit:module-index <模块路径>
```

不要默认假设裸 `/design`、`/tasks`、`/impl`、`/module-index` 一定可用。

### `/autolearn-sdd-kit:impl` 的状态与并行语义

- `/autolearn-sdd-kit:impl <需求名>` 会继续使用 Claude Code 内置任务系统追踪本次会话内进度，同时把跨会话可见的执行快照写回 `.claude/tasks/<需求名>.tasks.md` 的固定 generated section（例如 `## Implementation Record`）。最终摘要推荐固定包含：`Requested mode`、`Parallel strategy`（`none` / `subagents`）、`Actual mode`、`Fallback reason`（如有）、`Status sync`、`Status file`。
- 该 generated section 只记录执行状态摘要；原始 Task 正文、`depends_on`、`files`、`steps`、`acceptance` 仍然视为 spec，不应被执行阶段改写。
- `/autolearn-sdd-kit:impl <需求名> --parallel` 的语义是：**请求使用多个 subagent 做安全的 best-effort 并行**，不是 Team 模式。
  - 只有当 top-level Task 的 `depends_on` 已满足，且 `files` 无重叠/无明显冲突时，才应该真正 fan-out 给多个 subagent。
  - 如果依赖关系或文件冲突使并行不安全，流程应自动降级为顺序执行，并明确报告 fallback 原因。
  - 默认不应创建长期协作 team；这里的并行更接近一次性 dispatch 多个 fresh subagent。
- 因此，`--parallel` 不是“保证提速”的开关；当任务本身串行依赖很强、或多个 Task 需要改同一批文件时，看起来就会像顺序执行。

### 已知限制

- 非交互 `-p/--print` 模式下，写入项目 `.claude/**` 往往会被当作 sensitive path 拦截，不适合拿来验证完整落盘链路。
- 要验证真实工作流（plan/tasks/experience/modules/rules 落盘），优先使用**真实交互会话**。
- 轻量知识命令（如 `/autolearn-sdd-kit:remember`、`/autolearn-sdd-kit:index-rebuild`、`/autolearn-sdd-kit:meta-maintainer`）在某些 provider / 会话环境下仍可能主要受运行时响应与上游限流影响，而不是插件逻辑本身。
- 当前插件已经通过真实会话验证的主链路见：`REAL_SESSION_VALIDATION.md`

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
