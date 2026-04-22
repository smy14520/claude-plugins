# 反模式

本技能绝对不能做的事情。每一条都是从先前设计（autolearn-sdd-kit、spf 等）中观察到的具体失败模式，或 Karpathy 的 LLM-Wiki 文章中警告过的陷阱。

---

## ❌ AP1 —— 向量检索 / 基于嵌入的搜索

**不要**构建或调用任何向量存储、嵌入模型或基于相似度的检索来处理 wiki 内容。

**原因**：Karpathy 的 LLM-Wiki 核心理念——wiki 本身就是检索机制。页面和 wikilink 提供结构化、显式、低噪声的访问方式。向量检索会引入：

- 相似但无关的片段（噪声）
- 不透明的"为什么检索到这个"（黑盒）
- 每次更新都需要重建索引（维护成本）

**正确做法**：通过 `index.md` → 根页面 → 子页面进行显式导航。

---

## ❌ AP2 —— 未经用户触发的自动摄入

**不要**自动摄入任何内容。绝不可以在 research / spec / task / impl 阶段静默创建页面。

**原因**："什么值得沉淀"的判断是用户的核心价值贡献。自动摄入会：

- 用噪声填充 wiki
- 让用户养成忽略 wiki 内容的习惯
- 使用户失去对 wiki 内容的掌控

**正确做法**：每次摄入都由明确的用户指令触发。不确定时，先询问。

**例外**：R1（摄入时自动更新根页面）可以接受，因为它是用户触发的摄入的副作用，不是独立操作。

---

## ❌ AP3 —— 文件名中的类型前缀

**不要**将文件命名为 `entity-xxx.md`、`concept-xxx.md`、`gotcha-xxx.md`、`decision-xxx.md`。

**只允许** `source-xxx.md` 前缀。

**原因**：文件名前缀会：

- 在命名时强制进行类型分类（往往为时过早）
- 使文件名不必要地变长
- 暗示"类型"是主要导航维度（实际上主题才是）
- 破坏 Obsidian 图谱视图的兼容性

**正确做法**：文件名 = 主题名。类型放在 frontmatter 中。

参考先例：luotwo/llm-wiki 正是这样做的。spf 没有这样做，反而制造了维护负担。

---

## ❌ AP4 —— Experience / module / rule 作为页面类型

**不要**创建类型为 `experience`、`module` 或 `rule` 的页面。

**原因**：

- **"Experience"** 过于宽泛——是 gotcha、决策和随机笔记的大杂烩，随时间推移会变得不可导航。
- **"Module"** 与 `entity` 重叠。每个代码模块都是 entity；将它们分开会造成虚假二分法。
- **"Rule"** 应该放在 `CLAUDE.md` 或 skill 中，而不是 wiki 里。wiki 描述存在什么/发生了什么；规则规定应该做什么。

**从旧版（autolearn-sdd-kit）的正确映射**：

| 旧版 | 新版 |
|------|------|
| `experience/*.md` | 拆分为 `gotcha-*` 和 `decision-*` 页面 |
| `modules/*.md` | 转换为带适当标签的 `entity` 页面 |
| `modules/INDEX.md` | 删除——由该系统的根页面替代 |
| `rules/*.md` | 移至 `CLAUDE.md` 或专用 skill |
| `gotchas/*.md` | 使用具体场景重命名（而非主题）——`xhs-signature-clock-skew` ✅ |

---

## ❌ AP5 —— MOC（内容地图）层级文件

**不要**创建独立的 `moc-xxx.md` 文件来聚合主题。

**原因**：MOC 在真实内容之上增加了额外的元层。维护成本：

- 每个新页面：决定它属于哪个 MOC
- MOC 本身不断积累——最终需要"MOC 的 MOC"
- 当主题边界发生变化时，MOC 需要重写

**正确做法**：根实体页面（带 `tags: [root]`）达到同样的目的。聚合是描述领域实体的自然副产品，不是额外的层级。

---

## ❌ AP6 —— entity 页面中的机械式代码转录

**不要**编写那些只复制单个代码文件已提供信息的 entity 页面。

**不应编写的内容示例**：

- `UserService` 的完整方法列表（IDE 已提供）
- API 端点的完整列表（OpenAPI spec 已提供）
- 数据库列的完整列表（schema 文件已提供）
- 配置项的完整列表（配置文件已提供）

**原因**：这类信息会：

- 随代码演进而过时
- 相比 `grep` 或 IDE 查找不增加任何价值
- 让读者困惑 entity 页面的用途到底是什么

**正确做法**：5 文件测试——只编写需要阅读 5+ 个文件才能重建的信息。参见 [page-types.md#entity](page-types.md)。

---

## ❌ AP7 —— 强跨文档耦合

**不要**在以下场景中：

- 在 `tasks/*.md` 中：写任何 `[[wikilink]]`——task 必须是自足的执行计划
- 在 `research/*.md` 中：大量交叉引用——research 是临时的，不是正式文档
- 在 `wiki/*.md` 中：写"必须先阅读 X 才能使用 Y"——wiki 的消费者自行决定跟随哪些链接

**原因**：强耦合迫使读者按预定路径阅读。用户的设计理念是用户主导；wikilink 是提示，不是命令。

**正确做法**：

| 文档 | Wikilink 策略 |
|------|------|
| `.claude/tasks/*.md` | ❌ 不得包含 wikilink |
| `.claude/research/*.md` | 🟡 最少量，临时性的 |
| `.claude/brainstorms/*.md` | 🟢 可以链接 wiki 作为背景 |
| `.claude/wiki/*.md` | ✅ 自由链接 |

---

## ❌ AP8 —— 技能间的隐式自动串联

**不要**将 wiki skill 设计为自动调用其他 skill（research / brainstorm / task / impl）。同样，不要让其他 skill 静默调用 wiki 操作。

**原因**：用户已明确选择了非流水线式的、用户主导的工作流。每个阶段转换都是用户的决策。

**正确做法**：

- Wiki skill 返回结果。用户决定下一步。
- 其他 skill 可以*提及* wiki 内容作为输入（例如 brainstorm skill 可以说"如需引用先前方案，请执行 wiki query"），但绝不静默调用 wiki 操作。

---

## ❌ AP9 —— 无时间戳

**不要**创建没有 `date:` frontmatter 的页面，也不要写入没有 `[YYYY-MM-DD HH:MM]` 前缀的 log.md 条目。

**原因**：`log.md` 是会话恢复的关键工具（源自 Karpathy 的原始文章）。没有时间戳：

- `grep "^## \[" log.md | tail -5` 不再有效
- 过时根页面检测（R1.5）不再有效
- "我们上周做了什么？"变得无法回答

**正确做法**：每次变更——ingest、lint、init——都包含时间戳。

---

## ❌ AP10 —— 隐式 schema 变更

**不要**静默修改 schema（本 SKILL.md 或 `references/*.md`）。任何关于页面结构的变更都必须公告。

**原因**：页面模板是契约。修改它们会使现有页面失效。

**正确做法**：如果 schema 需要演进（例如添加新的必填 frontmatter 字段），要么：

- 迁移所有现有页面（小型 wiki 首选），或
- 标记新要求仅适用于新页面，并在 log.md 中记录切换时间点

---

## 汇总表

| # | 反模式 | 技能中的防护措施 |
|---|------|------|
| AP1 | 向量检索 | 技能逻辑仅使用显式导航 |
| AP2 | 自动摄入 | 每次摄入都需要用户触发指令 |
| AP3 | 文件名类型前缀 | 命名验证器拒绝 `entity-`、`concept-`、`gotcha-`、`decision-` 前缀 |
| AP4 | Experience/module/rule 类型 | 类型枚举严格限制为 5 个值 |
| AP5 | MOC 层级 | 根页面是带 `root` 标签的普通 entity，不是独立文件 |
| AP6 | 机械式转录 | entity 契约中的 5 文件测试（page-types.md） |
| AP7 | 强耦合 | Wikilink 策略表按惯例执行 |
| AP8 | 隐式技能串联 | Wiki skill 是无状态的——返回结果，不调用其他 skill |
| AP9 | 缺失时间戳 | Frontmatter `date:` 为必填；log.md 格式强制执行 |
| AP10 | 隐式 schema 变更 | Schema 变更必须显式记录 |
