---
name: "Wiki-CLI: 个人知识图谱与体检引擎 (Large System)"
description: "开发复杂本地 Markdown 维基内核与 CLI，支持双向链接、倒排索引、死链/孤岛体检，考察工单拆分与大工程协作"
type: e2e
prompt: "用 Python 构建一个个人本地 Markdown Wiki 知识库工具（wiki-cli）：支持 [[页面名称]] 双向链接解析与反向引用查询、正文 #tag 提取与聚合、基于标题与内容的关键词全文检索，以及知识库健康体检命令（扫描死链与无任何引用的孤岛页面）。纯本地文件驱动，不依赖外部数据库。"
setup_project: true
max_turns: 35
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
开发一个单机 Python 本地 Markdown 知识库管理工具与内核（`wiki-cli`），具备知识图谱双向链接与索引体检能力。

## 2. 存储与架构要求 (Constraints)
- **纯本地文件**：以指定目录下的 `.md` 文件作为物理载体，元数据与索引保存在单个 `.wiki_index.json` 或内存构建；
- **绝对禁令**：坚决不要引入 SQLite、向量数据库或外部全文检索服务（如 Elasticsearch）；
- **深模块架构**：区分解析器（Parser）、图拓扑索引（LinkGraph）、全文检索（SearchEngine）与 CLI 展示层。

## 3. 功能范围 (Scope)
- **双向链接解析**：
  - 支持解析 Markdown 中的 Wikilinks 语法：`[[目标页面]]` 或 `[[目标页面|显示别名]]`；
  - 提供反向引用查询（Backlinks）：查询引用了某页面的所有前置页面列表。
- **标签提取与聚合**：
  - 自动扫描解析正文中的 `#tag` 标签，支持按标签聚合文档。
- **全文检索 (FTS)**：
  - 支持关键词搜索（页面标题匹配优先，正文内容带上下文摘要）。
- **知识库健康体检 (Audit / Doctor)**：
  - 发现死链（Dead Links）：正文中链接了但物理文件不存在的页面；
  - 发现孤岛页面（Orphans）：没有任何其他页面链接指向的独立页面。

## 4. 边界约束 (Out of Scope)
- 坚决不做 Web 服务、实时渲染预览或富文本编辑器；
- 坚决不做远程 Git 自动推送同步；
- 坚决不做多用户权限控制。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是负责基础平台与开发者工具的首席架构师。
- 认可这是一个具备跨模块协作特征的大工程；
- 若开发者在把关点 1 识别出复杂度、提出将任务拆分为规范工单（Tickets）并按图推进，表示赞同与鼓励。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **多切片工单治理（Work Breakdown & Tickets）**：
  - 面对跨模块大工程，开发者是否通过 `/to-spec` 和 `/to-tickets` 将任务拆分为有依赖关系的工单？还是试图一口气把数千行代码盲写在一个文件里？
- **子系统职责边界（Subsystem Seams）**：
  - Parser、Graph、Search、Health 四个核心子系统是否高内聚低耦合？
- **中文与边界鲁棒性**：
  - 是否对中文文件名、中英文混合、大小写不敏感（Case-insensitive）提供了健壮支持？
