# wiki-cli

个人本地 Markdown 知识库命令行工具的统一语言。本词汇表是 wiki-cli 全部领域概念的唯一官方命名来源。

## Language

### 知识库结构

**Vault**:
wiki-cli 所管理的 Markdown 文件根目录；一个 Vault 即一个完整的个人知识库，所有命令都以它为工作对象。
_Avoid_: 知识库目录, workspace, 仓库, 笔记库

**Page（页面）**:
Vault 中的一个 `.md` 文件；其文件名去掉 `.md` 后缀即页面名，页面名在 Vault 内唯一标识一个 Page。
_Avoid_: 笔记, note, 文档, entry, 条目

### 链接体系

**Link（链接）**:
Page 正文中 `[[页面名]]` 语法指向目标 Page 的引用。"双向"是 Link 与 Backlink 合成后的能力，不存在名为"双向链接"的实体。
_Avoid_: 双向链接, 出链, 正向链接, outgoing link

**Backlink（反向引用）**:
Vault 中其他 Page 的 Link 指向本 Page 的反向视图；backlinks 查询回答"谁链接到我"。
_Avoid_: 反链, 入链, inbound link, back-reference

**Dead Link（死链）**:
指向 Vault 内不存在 Page 的 Link。
_Avoid_: 断链, broken link, 悬空链接, 失效链接

**Orphan（孤岛页面）**:
不被任何其他 Page 的 Link 指向的 Page（入度为零）。
_Avoid_: 孤儿页面, 孤页, isolated page, 独立页

### 标注与发现

**Tag（标签）**:
Page 正文中 `#tag` 语法声明的主题标记，用于跨 Page 聚合；与 Markdown 标题的 `#` 无关。
_Avoid_: 话题, topic, 分类, category, hashtag

**Keyword Search（关键词检索）**:
按标题与正文文本做大小写不敏感的子串匹配来查找 Page 的能力；多个关键词同时命中（AND）。
_Avoid_: 全文搜索, fts, 模糊搜索, fuzzy search

### 体检

**Health Check（健康体检）**:
doctor 命令对 Vault 的整体扫描报告：Dead Link 清单、Orphan 清单与冲突/汇总统计。
_Avoid_: lint, audit, 巡检
