# wiki-cli

个人本地 Markdown Wiki 知识库工具的统一语言词汇表。本文件只收领域名词，不含实现细节。

## Language（领域统一语言表）

**Vault（知识库）**:
wiki-cli 所操作的本地 Markdown 目录，是一切 Page 与链接的唯一根语境。
_Avoid_: 仓库、repo、workspace、站点

**Page（页面）**:
Vault 内的一个 Markdown 文件，以去掉 `.md` 后缀的文件名为身份。
_Avoid_: 文档、笔记、entry、文件

**Wiki Link（wiki 链接）**:
Page 正文中的 `[[目标]]` 引用语法，可带别名（`[[X|显示文字]]`）与子路径（`[[dir/X]]`）。
_Avoid_: 双向链接（"双向"只是出链与反链两个视角，不是独立概念）、markdown 链接

**Outgoing Link（出链）**:
某个 Page 通过 Wiki Link 指向的其他 Page。
_Avoid_: 外链（外链指 http 等外部 URL，本工具不将其解析为 Wiki Link）

**Backlink（反向引用）**:
指向某个 Page 的全部 Wiki Link 的来源 Page 集合。
_Avoid_: 入链、反链、被引用

**Dead Link（死链）**:
解析不到任何 Page 的 Wiki Link。
_Avoid_: 断链、broken link、失效链接

**Ambiguous Link（歧义链接）**:
裸文件名匹配到多个同名 Page、无法唯一解析的 Wiki Link。
_Avoid_: 冲突链接、重名链接

**Orphan Page（孤岛页面）**:
没有任何 Backlink 指向的 Page。
_Avoid_: 孤儿页面、孤立页面、isolated page

**Tag（标签）**:
正文中以 `#` 紧跟非空白开头的主题标记，可用 `/` 嵌套（如 `#parent/child`）。
_Avoid_: 分类、category、label、话题

**Doctor（健康体检）**:
对 Vault 一次性报告 Dead Link、Ambiguous Link 与 Orphan Page 的只读诊断。
_Avoid_: lint、audit、扫描报告
