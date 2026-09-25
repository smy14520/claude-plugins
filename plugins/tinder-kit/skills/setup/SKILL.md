---
name: setup
description: 为当前仓库初始化工程技能环境：配置本地 Markdown 工单驱动（.forge/）、分流标签、受控标签词典与领域模型规范，建立统一的驱动契约。在首次使用工程技能前执行。
disable-model-invocation: true
---

# Setup Project — 项目工程环境与驱动初始化

为本仓库脚手架化工程技能运行所需的外部契约与项目标准：

- **Issue tracker（本地工单驱动）** — 统一在本地 `.forge/` 目录下以纯 Markdown 文件管理 Spec 与工单，零外部网络依赖，纯透明可审计；
- **Triage labels（分流标签）** — 5 个标准分流角色对应的标签词汇；
- **Domain docs（领域文档规范）** — `.forge/CONTEXT.md` 统一词汇表与 `.forge/wiki/decision/` ADR 库的存放规则与读取协议；
- **Wiki tags（受控标签词典）** — `.forge/wiki/tags.md` 作为标签唯一真实源，防范同义词爆炸。

这是一个纯提示词驱动的对话式技能（Prompt-driven），不是确定性脚本。先探查环境现状，向人类汇报发现并确认草案，最后安全写入标准配置。

---

## 执行流程

### 1. 探查代码库现状（Explore）
首先使用环境探测工具检查当前仓库实际状态，查证已有事实，绝不凭空假设：
- 检查项目根目录是否存在 `CLAUDE.md` 或 `AGENTS.md`；若存在，检查其中是否已有 `## Agent skills` 章节；
- 检查是否存在 `.forge/` 目录以及其中的既有文档；
- 检查是否存在根目录 `.forge/CONTEXT.md` 与 `.forge/wiki/decision/`（若不存在则保持静默，绝不预建空模板）；
- 检查是否存在多包 Monorepo 信号（如 `pnpm-workspace.yaml`, `workspaces` 字段，或包含独立子包的 `packages/*`）。

### 2. 向人类汇报并逐项确认（Present findings and ask）
向人类结构化汇报当前发现，默认推荐并确认：
- **工单管理（Issue Tracker）**：默认采用 **Local Markdown 驱动**，所有需求草稿、Spec 与工单文件存放在本地 `.forge/` 下，由 AI 原生直接读写，无外部依赖；
- **分流标签（Triage labels）**：采用 5 种标准分流角色（`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`）；
- **领域文档（Domain docs）**：单上下文结构（`.forge/CONTEXT.md` 词汇表 + `.forge/wiki/decision/` ADR 库，按需延迟创建）；
- **Wiki 知识库与标签词典（Wiki & Tags）**：`.forge/wiki/` 存放避坑指南、架构决策与跨文件链路；生成初始 `.forge/wiki/tags.md`，内容随项目开发动态自生长。

### 3. 生成草案并供人类审阅（Confirm and edit）
向人类展示即将写入的配置清单草稿，等待人类确认或一句话微调：
- 待写入宿主文件（`CLAUDE.md` 或 `AGENTS.md`）的 `## Agent skills` 指针段落预览；
- `.forge/issue-tracker.md` 内容预览（以 [issue-tracker.md](./issue-tracker.md) 模板为起点）；
- `.forge/domain.md` 内容预览（以 [domain.md](./domain.md) 模板为起点）；
- `.forge/triage-labels.md` 内容预览（以 [triage-labels.md](./triage-labels.md) 模板为起点）；
- `.forge/wiki/tags.md` 内容预览（以 [tags.md](./tags.md) 模板为起点）。

### 4. 安全落盘（Write）
得到人类确认后执行写盘：

1. **选择宿主文件（Pick the file to edit）**：
   - 若 `CLAUDE.md` 存在，编辑它；
   - 否则若 `AGENTS.md` 存在，编辑它；
   - 若两者均不存在，询问人类希望创建哪一个（推荐：`CLAUDE.md`），绝不擅自多建。

2. **原地更新指针（In-place update，保证幂等）**：
   - 检查目标宿主文件中是否已存在 `## Agent skills` 章节；
   - **若已存在**：使用 `Edit` 工具在原位置替换其内容，保持其上下方的其他规则原封不动，**绝不追加重复段落**；
   - **若不存在**：在文件末尾追加：
     ```markdown
     ## Agent skills

     ### Issue tracker
     Local markdown issue tracker. See `.forge/issue-tracker.md`.

     ### Triage labels
     Standard triage labels. See `.forge/triage-labels.md`.

     ### Domain docs
     Single-context layout: CONTEXT.md in .forge/, ADRs in .forge/wiki/decision/. See `.forge/domain.md`.

     ### Wiki
     Project knowledge base, gotchas, and architectural decisions. See `.forge/wiki/tags.md` and `.forge/wiki/index.md`. Use `/wiki` skill to search or contribute.
     ```

3. **落盘协议文档与标签注册表**：
   以本技能目录下的初始模板文件为真实基准，使用 `Write` 工具写入 `.forge/`：
   - `.forge/issue-tracker.md`：写入 [issue-tracker.md](./issue-tracker.md) 内容；
   - `.forge/domain.md`：写入 [domain.md](./domain.md) 内容；
   - `.forge/triage-labels.md`：写入 [triage-labels.md](./triage-labels.md) 内容；
   - `.forge/wiki/tags.md`：写入 [tags.md](./tags.md) 内容（受控标签真实源与打标/检索铁律）。

*(注意：极度遵循懒创建哲学，此时绝对不要创建带有虚假/占位内容的 `.forge/CONTEXT.md` 或假 ADR，全交由后续技能在真正敲定术语和架构时延迟创建！)*

### 5. 完工告知与去神秘化（Done）
告知人类初始化已圆满就绪：
- 所有工程技能（`/grill-with-docs`、`/implement`、`/wayfinder`、`/to-spec`、`/to-tickets`、`/code-review`）后续将自动遵循这些规范驱动；
- 这些协议全都是纯 Markdown 文档，人类可以随时在 VS Code 中直接手改调优，无需重新运行此技能。
