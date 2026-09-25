# CONTEXT — 统一语言词汇表

本文件是 wiki-cli 项目的核心统一语言（Ubiquitous Language）真实源。
所有工单标题、代码命名、测试用例名、CLI 输出必须严格采用下列术语。

## 核心术语

### Vault（知识库根）
一个目录，包含全部 Markdown 页面与单一索引文件 `.wiki_index.json`。一个 Vault = 一个自包含、可整体拷走的知识库。CLI 通过 `--root` 定位，缺省为当前目录。
_Avoid_: workspace、知识库目录、repo（指 vault 时）

### Page（页面）
Vault 内任意一个 `.md` 文件（递归发现，跳过 `.` 开头的隐藏目录）。

### PageName（页面名）
文件名去掉 `.md` 后缀。全 Vault 唯一、**大小写不敏感**（匹配用 casefold），子目录层级不进入链接语义（见 ADR-0001）。
_Avoid_: slug、标题、文件路径

### WikiLink（双向链接）
`[[PageName]]` 或 `[[PageName|alias]]` 形式的链接。别名仅供显示，索引只记 Target。出现在 fenced code block 与行内代码中的 `[[...]]` **不是** WikiLink。
_Avoid_: markdown 链接（`[text](url)` 不是 WikiLink）、双链

### Backlink（反向引用）
指向某 Page 的全部 WikiLink 所在的来源 Page 集合。由索引派生，非独立存储。

### Tag（标签）
正文中 `#` 引导的行内标记，支持中文与 `.`/`/` 层级分隔（`#lang/python`，聚合时父标签包含子标签计数）。排除：ATX 标题记号本身、fenced code block 与行内代码内、URL 片段 `#anchor`（见 `.forge/wiki/decision/0003` 词法定义）。
_Avoid_: hashtag、分类（指 tag 时）、label

### Index（索引）
Vault 根下**单一** JSON 文件 `.wiki_index.json`，由 `build` 命令生成/增量更新；查询的**计算路径只读索引**（摘要渲染由 CLI 层读命中页原文，见 ADR-0004 修订）。原子写入（tmp + `os.replace`）。严禁 SQLite 或任何外部检索服务（见 ADR-0002）。
_Avoid_: db、数据库、cache

### Doctor（体检）
报告 DeadLink 与 Orphan 的诊断命令；发现任一问题时退出码为 1（CI 友好）。

### DeadLink（死链）
指向不存在 PageName 的 WikiLink。

### Orphan（孤岛页面）
**无任何入链**的 Page（`--entry` 指定的入口页豁免）。注意：只出不进的悬空叶子页也算 Orphan。
_Avoid_: 孤立文件、unlinked page
