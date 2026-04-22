# 操作：Ingest / Query / Lint

三个基本操作的详细流程。SKILL.md 提供高层步骤；本文件提供包含边界情况的完整工作流程。

---

## Ingest

将新知识提炼为 wiki 页面。始终由用户触发，从不自动执行。

### 触发指令（用户意图）

- "记一下这个坑" / "记录这个经验"
- "沉淀一下 xxx" / "把 xxx 加到 wiki"
- "这个决定值得记下来"
- "让 wiki 收录这个"

### 完整流程

**步骤 1 —— 分类类型**

使用 [page-types.md#type-decision-tree](page-types.md) 中的决策树：

1. 外部原始资料？→ `source`
2. 具体场景 + 错误 + 修复方案？→ `gotcha`
3. 在多个方案中选择某个方案的理由？→ `decision`
4. 去掉所有专有名词后仍然说得通？→ `concept`
5. 本项目中的真实对象？→ `entity`

如果模糊，**优先选择更具体的类型**（gotcha > decision > entity > concept）。

**步骤 2 —— 确定文件名**

从用户描述中提取主题。转换为 **kebab-case，全部小写**。

- Gotcha：命名场景，而非主题。`xhs-signature-clock-skew` ✅，`xhs-api-issue` ❌
- Decision：命名选择。`webhook-vs-poll-for-xhs` ✅，`xhs-integration` ❌
- Entity：命名实体。`xhs-api`, `user-service`
- Concept：命名模式。`idempotent-webhook`, `optimistic-lock`
- Source：加 `source-` 前缀。`source-xhs-api-doc`

**步骤 3 —— 检查是否已存在**

```bash
ls .claude/wiki/<filename>.md
```

如果已存在：

提示用户："页面 `<filename>.md` 已存在。要 (a) 合并到现有页面，(b) 创建新页面（改名），还是 (c) 取消？"

等待用户选择后再继续。

**步骤 4 —— 应用模板**

从 [page-types.md](page-types.md) 加载匹配类型的模板。根据用户描述填充。

**重要**：不要要求用户逐项填写每个模板段落。从其描述中推断能填充的内容；用户未涉及的部分保留为 `_(待补充)_` 占位符，并在摘要中注明。

**步骤 5 —— 确定归属根页面**

扫描新页面的 `tags:` frontmatter。对每个标签：

```bash
grep -l "tags:.*\b<tag>\b" .claude/wiki/*.md | xargs grep -l "tags:.*\broot\b"
```

候选者是标签有重叠的根页面。

如果恰好一个匹配 → 即为归属根页面。
如果零匹配 → 页面为孤立（暂时）；不要自动创建根页面，只需注明。
如果 2+ 匹配 → 优先选择标签重叠最多的根页面；如果仍然模糊，询问用户。

**步骤 6 —— 更新归属根页面（R1）**

详细规则见 [maintenance-rules.md#r1](maintenance-rules.md)。简版：

- 在根页面的对应段落（已接入渠道 / 设计模式 / 已知陷阱 / 等）中插入 wikilink
- 如果变更是重大变更，在版本演进中追加一行
- **绝不重写已有根页面内容**——只追加

**步骤 7 —— 追加到 log.md**

单行格式：

```
## [YYYY-MM-DD HH:MM] ingest | <type>: <name>
<optional one-line note>
```

**步骤 8 —— 输出摘要**

```
✅ Ingest 完成

- 新建页面: .claude/wiki/<name>.md (<type>)
- 归属 root: [[<root-name>]] (已更新)
- 待补充段落: <section-a>, <section-b>
- Log: 已追加
```

### 边界情况

**情况：用户说"记一下"但细节不足**

提出一个有针对性的问题以确定类型和关键内容。绝不摄入只有标题没有正文的页面。

好问题："这个坑的触发条件是什么？错误信息是什么？"
坏问题："请填写以下所有字段..."

**情况：页面已涵盖该主题但用户想添加新信息**

优先**追加到现有页面**而非创建新页面，除非新信息是独立的 gotcha/decision。将现有页面视为活文档，而非固定文档。

**情况：摄入过程中发现应该存在新的根页面**

如果在摄入过程中发现多个现有页面共享一个领域但没有根页面，不要主动创建根页面。完成当前摄入后提示："注意到 `<tag>` 领域已有 5+ 相关页面但无 root，建议考虑创建 root 页面 `<name>.md`。"

---

## Query

为特定任务（例如 brainstorm 起草）检索知识。只读操作。

### 触发指令

- "参考 wiki 里的 X"
- "查一下 wiki 有没有 X"
- "X 之前做过类似的吗"
- "wiki 里 X 是怎么设计的"

### 完整流程

**步骤 1 —— 读取 index.md**

```bash
cat .claude/wiki/index.md
```

识别五个段落中的相关条目：

- 🏠 根实体 —— 匹配查询的系统级入口
- 🧠 跨域通用模式 —— 匹配查询的抽象模式
- 📋 跨系统决策 —— 跨领域决策
- 📜 Source 摘要 —— 原始资料引用
- ⚠️ 孤立页面 —— 未分类页面（最后检查，可能包含相关内容）

**步骤 2 —— 读取根页面**

对每个相关的根页面，完整读取。注意核心模块 / 已接入渠道 / 关键决策 / 设计模式 / 已知陷阱 / 等段落下分组的 wikilink。

**步骤 3 —— 选择性跟踪 wikilink**

不要读取每个 wikilink。运用判断：

- 读取 2-3 个类似子实体通常有用（例如做 `xhs` 工作时，读取 `wechat-api` 和 `douyin-api` 作为类比）
- 读取 1-2 个关键 gotcha 有助于发现复现模式
- 读取 1 个关键 decision 可解释架构背后的"为什么"
- 跳过明显与当前查询无关的 wikilink

**步骤 4 —— 同时读取 index.md 中的跨域页面**

如果查询涉及抽象模式，即使该模式已从根页面链接，也要读取跨域 concept/decision。

**步骤 5 —— 输出结构化摘要**

对每个 `已读取` 条目按 [R5-freshness](maintenance-rules.md#r5) 标注新鲜度提示。从页面的 `date:` frontmatter 计算年龄（如果存在），否则使用文件系统 mtime。

- `< 90 days`：无标注
- `90–180 days`：`(X months ago)` —— 中性
- `180–365 days`：`(X months ago ⚠️)` —— 黄色警告
- `> 365 days`：`(X months ago ⚠️ stale)` —— 强警告
- `source-*.md` 或 `tags: [evergreen]`：不标注

```
📚 Wiki Query: "<original query>"

### 已读取
- [[ai-customer-service]]                系统导航                    (2 weeks ago)
- [[wechat-api]]                          类比渠道                    (3 months ago)
- [[wechat-signature-clock-skew]]        签名类坑                    (8 months ago ⚠️)
- [[idempotent-webhook]]                  webhook 幂等模式             (1 year ago ⚠️ stale)

### 关键发现
- 点1（含引用）
- 点2（含引用）

### 未读取但可能相关
- [[douyin-concurrent-reply-risk]] — 如需并发控制再读
- [[source-wechat-customer-api-doc]] — 如需 API 细节

### 新鲜度提示
有 2 页标注 ⚠️（> 180 天未更新）。建议阅读时核对与当前代码/决策是否仍一致。
```

### 边界情况

**情况：用户未指定范围，只说"参考 wiki"**

提一个澄清问题："参考 wiki 里的哪方面？是架构决策、具体模块、踩过的坑，还是抽象模式？"

**情况：未找到相关页面**

输出："Wiki 中未找到与 `<query>` 相关的页面。建议：在 research 阶段完成后再 ingest 相关发现。"

**情况：存在相关页面但已过时**

由 R5-freshness 内联标注处理（见步骤 5）。无需单独的边界情况处理——年龄提示现在是每次 Query 输出的标准部分。

---

## Lint

审计 wiki 健康度。除更新 `index.md` 孤立页面段落外，均为只读操作。

### 触发指令

- "wiki 体检"
- "wiki 健康检查"
- "wiki lint"
- "清理一下 wiki"

### 完整流程

**步骤 1 —— 扫描孤立页面**

不被任何其他页面引用的非根页面：

```bash
# Pseudocode
for each page in wiki/ (excluding index.md, log.md, root pages):
    if no other page contains [[<page-name>]]:
        mark as orphan
```

**步骤 2 —— 扫描断裂 wikilink**

指向不存在页面的 wikilink：

```bash
# Extract all [[xxx]] references and verify xxx.md exists
```

**步骤 3 —— 扫描过时根页面**

最后更新时间早于其某个子页面创建时间的根页面（表明子页面已添加但根页面未更新——R1 违规）：

```bash
for each root in wiki/ (tags contains root):
    root_mtime = stat(root).mtime
    for each child linked in root:
        if child_ctime > root_mtime and child not in root's wikilinks:
            flag as stale root
```

**步骤 4 —— 扫描重复候选**

文件名高度相似的页面（文件名 > 10 个字符时 Levenshtein 距离 ≤ 3）：

```bash
# e.g. xhs-signature-clock-skew.md vs xhs-signature-timing-skew.md
```

这些是人工审查信号，不自动合并。

**步骤 5 —— 晋升候选（R3）**

被 5+ 个其他页面引用但缺少 `root` 标签的页面：

```bash
for each page:
    count = sum([1 for other in wiki/ if contains [[<page>]] in other])
    if count >= 5 and 'root' not in tags:
        suggest promotion
```

**步骤 6 —— 按年龄审查候选（R5）**

扫描所有非豁免页面，查找年龄 > 180 天的页面：

```bash
for each page in wiki/ (excluding source-*.md, pages tagged 'evergreen'):
    age = now - (page.date frontmatter || page mtime)
    if age > 180 days:
        classify as 'mild' (180-365) or 'strong' (> 365)
        add to review-candidates list
```

**这些是信号，不是错误。** 它们出现在报告的独立段落中；不会阻断提交，也不意味着页面有错。

**步骤 7 —— 更新孤立页面段落**

用最新的孤立列表覆盖 `index.md` 的 ⚠️ 孤立页面段落。不要修改其他段落。

**步骤 8 —— 追加到 log.md**

```
## [YYYY-MM-DD HH:MM] lint | orphans=N, broken=M, stale-roots=K, dup-candidates=L, review-candidates=R
```

**步骤 9 —— 输出报告**

报告分为**两个严重程度级别**：

- ❌ **实际问题**——结构性损坏，必须修复
- ⚠️ **审查候选**——值得查看的信号，但没有损坏（用户决定）

```
🧹 Wiki Lint Report

## ❌ Real issues (N + M + K + L)

### Orphans (N)
- [[xxx]] — created YYYY-MM-DD
- [[yyy]] — created YYYY-MM-DD

### Broken wikilinks (M)
- [[zzz]] referenced in [[aaa]] — no such page exists

### Stale roots (K)
- [[root-a]] — last updated YYYY-MM-DD, child [[bbb]] created later

### Duplicate candidates (L)
- [[xxx-foo]] vs [[xxx-bar]] — similar filenames, review manually

## ⚠️ Review candidates (R) — age-based, not broken

Per [R5-freshness](maintenance-rules.md#r5). These pages are old enough that their content may no longer reflect the current state of the code/decisions. Decide case-by-case:
1. Still valid → no action, or re-read and update `date:` to refresh
2. Outdated but kept for history → add `deprecated: true` frontmatter
3. Fully obsolete → delete

### Mild (180–365 days)
- [[decision-hmac-algo]]   8 months ago
- [[xhs-signature-clock-skew]]   6 months ago

### Strong (> 365 days)
- [[idempotent-webhook]]   1 year 4 months ago
- [[entity-old-crm]]   2 years ago

## 💡 Promotion candidates (R3)
- [[ccc]] — referenced by 7 pages, consider adding `root` tag

## Recommended next steps
- Fix real issues first (orphans / broken / stale-roots / duplicates)
- Then review candidates in descending age
```

### 边界情况

**情况：wiki 为空或接近为空（<5 页）**

跳过 lint 并提示："Wiki 页面过少（<5），暂无需体检。"

**情况：孤立页面过多（>30% 的总页面数）**

发出强烈警告：

```
⚠️ WARNING: 孤立页面占比 X%（> 30%），wiki 组织可能失控。
建议：(a) 集中做一次整理，把孤立页面归属到 root；(b) 考虑是否某些孤立页面本应是 root。
```
