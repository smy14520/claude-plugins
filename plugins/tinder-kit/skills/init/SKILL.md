---
name: init
description: 为当前仓库初始化工程技能环境：配置本地 Markdown 工单驱动（.forge/）、分流标签与领域模型文档规范，建立统一的驱动契约。在首次使用工程技能前执行。
disable-model-invocation: true
---

# Setup Project — 项目工程环境与驱动初始化

为本仓库脚手架化工程技能运行所需的外部契约与项目标准：

- **Issue tracker（本地工单驱动）** — 统一在本地 `.forge/` 目录下以纯 Markdown 文件管理 Spec 与工单，零外部网络依赖，纯透明可审计；
- **Triage labels（分流标签）** — 5 个标准分流角色对应的标签词汇；
- **Domain docs（领域文档规范）** — `.forge/CONTEXT.md` 统一词汇表与 `.forge/wiki/decision/` 的 ADR 存放规则与读取协议。

这是一个纯提示词驱动的对话式技能（Prompt-driven），不是确定性脚本。先探查环境现状，向人类汇报发现并确认，最后写入标准配置。

---

## 执行流程

### 1. 探查代码库现状（Explore）
首先使用环境探测工具检查当前仓库实际状态，查证已有事实，绝不凭空假设：
- 检查项目根目录的 `CLAUDE.md` 或 `AGENTS.md`：是否存在？是否已有 `## Agent skills` 章节？
- 检查是否存在 `.forge/CONTEXT.md` 与 `.forge/wiki/decision/`；
- 检查是否存在 `.forge/` 目录；
- 检查是否存在多包 Monorepo 信号（如 `pnpm-workspace.yaml`, `workspaces` 字段，或包含独立子包的 `packages/*`）。

### 2. 向人类汇报并确认配置（Present findings and ask）
向人类结构化汇报当前发现，默认推荐并确认：
- **工单管理（Issue Tracker）**：默认采用 **Local Markdown 驱动**，所有需求草稿、Spec 与工单文件存放在本地 `.forge/` 下，由 AI 原生直接读写，无外部依赖；
- **分流标签（Triage labels）**：采用 5 种标准分流角色（`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`）；
- **领域文档（Domain docs）**：单上下文结构（`.forge/CONTEXT.md` 词汇表 + `.forge/wiki/decision/` ADR 库）。

### 3. 生成与确认草案（Confirm and edit）
向人类展示即将写入的配置清单：
- `docs/agents/issue-tracker.md` 内容（本地 Markdown 工单规范）；
- `docs/agents/domain.md` 内容（领域模型与 ADR 规范）；
- `docs/agents/triage-labels.md` 内容；
- 即将写入 `CLAUDE.md`（或 `AGENTS.md`）的 `## Agent skills` 导航指针。

### 4. 落盘配置（Write）
得到人类确认后执行写盘：

1. **落盘驱动文档**：
   在项目根目录确保 `.forge/` 目录存在，将确认后的三份文档写入：
   - `.forge/issue-tracker.md`
   - `.forge/domain.md`
   - `.forge/triage-labels.md`
2. **挂载指针至项目 `CLAUDE.md`**：
   优先编辑既有的 `CLAUDE.md`（若无则创建），在文件末尾追加标准前置指针：
   ```markdown
   ## Agent skills

   ### Issue tracker
   Local markdown issue tracker. See `.forge/issue-tracker.md`.

   ### Triage labels
   Standard triage labels. See `.forge/triage-labels.md`.

   ### Domain docs
   See `.forge/domain.md` and `.forge/CONTEXT.md`.
   ```

### 5. 初始化收尾（Done）
告知人类初始化已就绪。所有工程技能（`/grill-with-docs`、`/implement`、`/wayfinder`、`/to-spec`、`/to-tickets`）即日起将自动通过 `.forge/` 与本地 Markdown 驱动。
人类可随时直接在 `.forge/` 查验或编辑所有工单与决策。
