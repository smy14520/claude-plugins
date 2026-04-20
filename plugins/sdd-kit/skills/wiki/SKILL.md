---
name: wiki
description: "Manage the project's persistent knowledge wiki at `.claude/wiki/` — structured pages with wikilinks, Karpathy LLM-Wiki pattern (NOT vector retrieval). Pages carry type=entity|concept|gotcha|decision|source in frontmatter; root pages (tag=root) serve as domain hubs. Three primitives: Ingest (record new knowledge), Query (read index → root → selective follow), Lint (orphans / broken links / stale roots). Invoke only on explicit user request (e.g. '用 wiki skill ingest / query / lint …')."
---

# Wiki — 持久化知识管理

将 `.claude/wiki/` 作为跨迭代的结构化知识图谱来管理。用户提供判断力和原始素材，本 skill 负责簿记工作。

## 定位

本 skill 是 Karpathy 三层 LLM-Wiki 架构中的 **schema 层**：

- 原始素材 → `.claude/research/`、代码、外部文档
- **Wiki（本 skill 维护）** → `.claude/wiki/`
- **Schema（本 SKILL.md + references/）** → 告诉 LLM 如何维护 wiki

**核心原则**：知识是*编译产物*，而非实时检索的结果。LLM 扮演图书管理员的角色。

## 三个原语

根据用户意图匹配对应原语。详细流程见 [references/operations.md](references/operations.md)。

### 🟢 Ingest — 提炼新知识

触发短语："记一下这个坑/经验/决定"、"sink into wiki"、"record this"。

流程（详见 `references/operations.md#ingest`）：

1. 分类类型（entity | concept | gotcha | decision | source）
2. 确定文件名（主题名称，kebab-case，不加类型前缀）
3. 检查页面是否已存在 → 若存在则提示用户选择合并还是新建
4. 从 [references/page-types.md](references/page-types.md) 应用模板
5. 按 [references/maintenance-rules.md](references/maintenance-rules.md#r1) 更新所属 root 页面
6. 在 `log.md` 追加一行记录
7. 输出摘要

### 🔵 Query — 回忆已有知识

触发短语："参考 wiki 里的 X"、"wiki 里有没有 X"、"have we done similar"。

流程：

1. 读取 `.claude/wiki/index.md` → 定位相关的 root 页面或跨领域页面
2. 读取 root 页面 → 扫描其分组 wikilink
3. 根据用户的实际需求有选择地跟踪 wikilink（不要全部读取）
4. 返回结构化摘要：已读页面、每页关键发现、相关但未读的线索

### 🟡 Lint — 审计 wiki 健康状况

触发短语："wiki 体检"、"wiki lint"、"clean up wiki"。

流程：

1. 扫描孤立页面（未被任何页面引用的非 root 页面）
2. 扫描失效 wikilink（指向不存在页面的链接）
3. 扫描过期 root 页面（root 页面最后更新时间早于某子页面的创建时间）
4. 扫描重复候选（文件名 Levenshtein 距离低于阈值）
5. 扫描**按年龄需要复查的页面**（超过 180 天的页面，参见 [R5-freshness](references/maintenance-rules.md#r5)）
6. 按 [references/maintenance-rules.md](references/maintenance-rules.md#r4) 更新 `index.md` 的孤立页面区段
7. 输出 markdown 格式报告，包含**两个严重级别**：⚠️ 复查候选（信号，非错误）vs ❌ 真正的问题（失效 / 孤立 / 重复）

## 目录结构

```
.claude/wiki/
├── index.md          # 导航（仅包含 root + 跨领域 + source + 孤立页面）
├── log.md            # 仅追加的操作日志
│
├── <root-topic>.md   # tag: [root] — 领域枢纽（如 ai-customer-service.md）
├── <topic>.md        # 以主题命名的页面（如 xhs-api.md、idempotent-webhook.md）
│
└── source-<name>.md  # 原始素材摘要（唯一允许的前缀）
```

## 核心规则（速查）

详细的设计理由和操作流程请参阅下方链接的 `references/` 文件。

1. **命名** — 文件名 = 主题名称，kebab-case 格式。**不加类型前缀**，`source-` 除外。参见 [references/page-types.md#naming](references/page-types.md)。
2. **类型写在 frontmatter 中，而非文件名** — 每个页面在 frontmatter 中都有 `type:` 字段（entity | concept | gotcha | decision | source）。
3. **root 页面负责聚合** — 带有 `tags: [root]` 的页面作为领域入口，按角色分组列出子页面的 wikilink。参见 [references/index-and-root.md](references/index-and-root.md)。
4. **index.md 保持精简** — 仅列出 root 页面、跨领域概念/决策、source 摘要和孤立页面。**禁止列出 root 的子页面**。参见 [references/index-and-root.md#index-rules](references/index-and-root.md)。
5. **entity 页面是聚合视图，而非代码镜像** — 记录那些需要阅读 5 个以上文件才能还原的信息；不要记录单个文件或 IDE 索引已经提供的信息。参见 [references/page-types.md#entity](references/page-types.md)。
6. **Wikilink 策略**：
   - ✅ Wiki 页面之间可自由链接
   - ✅ Spec 文件可以链接到 wiki 页面（作为背景提示）
   - ❌ **Task 文件禁止包含 wikilink**（执行计划必须自包含）
   - ❌ Research 笔记很少需要 wikilink（临时性质）

## 初始化

若 `.claude/wiki/` 不存在，则从 [assets/templates/](assets/templates/) 创建种子文件：

```
.claude/wiki/index.md    ← 来自 assets/templates/index.md
.claude/wiki/log.md      ← 来自 assets/templates/log.md
```

创建完成后，在 `log.md` 中追加：

```
## [YYYY-MM-DD HH:MM] init | wiki initialized
```

## 本 skill 不做的事

- 不执行向量搜索或基于嵌入的检索（这是有意为之 — 参见 Karpathy LLM-Wiki 设计思路）
- 不自动 ingest（每次 ingest 必须由用户触发）
- 不存储规则/风格指南/PSR 标准（那些属于 `CLAUDE.md` 或其他 skill）
- 不创建以 `experience-*`、`module-*`、`rule-*` 为分类名称的页面（这些都是反模式 — 参见 [references/anti-patterns.md](references/anti-patterns.md)）

## 何时不激活

当用户出现以下情况时，不要运行本 skill：

- 提问的问题无需 wiki 上下文即可直接回答
- 正在进行与结构化知识无关的小范围本地编辑（bug 修复、样式调整）
- 明确选择退出（"don't touch the wiki"、"skip wiki"）

拿不准时，运行 **Query**（只读、成本低），而非 **Ingest**。
