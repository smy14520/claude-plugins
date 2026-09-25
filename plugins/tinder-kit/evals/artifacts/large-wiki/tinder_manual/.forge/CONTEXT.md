# CONTEXT — 统一语言词汇表

本项目统一语言（Ubiquitous Language）的唯一真实源：工单标题、架构假设、测试用例名与代码命名必须使用此处定义的标准术语，严禁漂移到 `_Avoid_` 负面清单中的同义词。本文件只沉淀概念语义，不记录实现细节。

## 核心概念

### 知识库（Wiki）
wiki-cli 所管理的本地 Markdown 文件集合：页面、页面间的双向链接与标签的总和。
_Avoid_: vault、仓库（易与 git repository 混淆）、笔记库

### 页面（Page）
知识库中的一个 Markdown 文件，以其文件名（去 `.md` 后缀）为唯一身份标识，大小写敏感；不读取 frontmatter title，不支持别名。
_Avoid_: 文档（document）、笔记（note）、条目（entry）

### 链接（Link）
页面正文中 `[[目标]]` 形式的页面级引用；`|` 后为显示文本（解析时丢弃），`#` 后为锚点/块引用（解析时剥离到页面级）。
_Avoid_: hyperlink、URL、超链接

### 反向引用（Backlink）
指向某页面的全部入链；页面链接自身不计入。
_Avoid_: back-reference、引用计数

### 出链（Outbound Link）
某页面指向其他页面的全部链接；无法解析的目标如实标记为死链。
_Avoid_: outgoing link、外链（易与外部 URL 混淆）

### 死链（Dead Link）
目标页面不存在的链接。
_Avoid_: broken link、断链、坏链

### 孤岛页面（Orphan）
零入链的页面；页面链接自身不计入，体检时可用豁免清单排除。
_Avoid_: 孤儿页、isolated page

### 重复标题（Duplicate Title）
多个页面文件使用同一文件名（去 `.md` 后缀）导致的身份歧义，属体检必报异常。
_Avoid_: 命名冲突、重名碰撞

### 体检（Doctor）
对知识库执行死链、孤岛页面、重复标题三类检查的健康诊断。
_Avoid_: lint、audit、健康检查

### 标签（Tag）
行内 `#tag` 或 frontmatter `tags:` 声明的分类标记；聚合时不区分大小写。
_Avoid_: category、topic、话题

### 检索（Search）
基于页面正文文本内容定位页面的查询方式，区别于沿链接图导航的查询（如反向引用）。语义：大小写不敏感的子串匹配，多个关键词之间为 AND。
_Avoid_: query、find、grep、搜索引擎

### 索引（Index）
从知识库文件推导出的派生查询数据，可整体丢弃并无损重建；它绝不是真实源，也不是需要维护状态的资产。
_Avoid_: database、DB、缓存

### 真实源（Source of Truth）
磁盘上的 Markdown 文件本身。索引等一切派生物与之冲突时，一律以真实源为准。
_Avoid_: 单一事实源、master data

### 代码围栏（Code Fence）
三反引号或三波浪线围起的区域；其中的链接与标签一律不计入图与聚合。
_Avoid_: 代码块（过宽，还包含行内代码的含义）
