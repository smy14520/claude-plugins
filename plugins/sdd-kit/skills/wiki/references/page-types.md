# 页面类型与内容契约

五种页面类型。每种有独特的用途和严格的内容契约。

## 命名约定（适用于所有类型）

- 文件名 = 主题名，使用 **kebab-case**，全部小写
- **无类型前缀**（❌ `entity-xxx.md`，❌ `gotcha-xxx.md`，❌ `concept-xxx.md`）
- **只允许 `source-` 前缀**（用于原始资料摘要页面）
- 类型信息放在 frontmatter 的 `type:` 字段中
- 主题名称应具体到领域，不要过于抽象（例如 `xhs-api.md`，不是 `external-api.md`）

示例：
- ✅ `ai-customer-service.md`, `xhs-api.md`, `idempotent-webhook.md`
- ✅ `xhs-signature-clock-skew.md`, `webhook-vs-poll-xhs.md`, `source-xhs-api-doc.md`
- ❌ `entity-xhs-api.md`, `gotcha-xhs-signature.md`, `decision-webhook.md`

## Frontmatter schema（所有类型通用）

```yaml
---
type: entity | concept | gotcha | decision | source
tags: [<domain>, <subdomain>, ...]
aliases: [<alt-name>, ...]     # optional, improves search
date: YYYY-MM-DD               # creation date (auto-set at ingest)
---
```

具有语义含义的特殊标签：

- `root` —— 此页面是领域枢纽（聚合子页面；列在 `index.md` 中）
- `cross-domain` —— 此页面可跨系统/项目复用（列在 `index.md` 中）

---

## type: entity

**定义**：具有状态、边界和版本的真实可识别对象。API、服务模块、数据库表、外部系统、队列、存储。

**经验法则**：你应该能回答"它*是*什么？"而不是"它是*怎么*工作的？"。

### 内容契约

**应编写的内容**（相比代码增加价值）：

- 跨文件信息聚合（分散在多个文件中的配置，分散在多个模块中的调用方）
- 代码中不可见的约束（速率限制、签名规则、并发限制、正确使用模式）
- 调用拓扑和模块边界
- 相关 decision / concept / gotcha 的链接

**不应编写的内容**（代码已提供）：

- API 端点列表（官方文档 / OpenAPI spec 已处理）
- 方法签名列表（IDE 已处理）
- 数据库列列表（schema 文件已处理）
- 配置项列表（配置文件已处理）

### 5 文件测试（硬性规则）

对 entity 页面上的每条信息，问：**"AI 需要阅读多少个文件才能从代码中重建这条信息？"**

- 1 个文件即可重建 → **不要写**（是噪声）
- 需要 5+ 个文件才能重建 → **写**（是真正的价值）

### 模板

```markdown
---
type: entity
tags: [<domain>, ...]
date: YYYY-MM-DD
---

# <Entity Name>

> Code entry: <path>
> Related: [[module-a]], [[module-b]]

## Responsibility boundary

Explicit 2-3 lines: what it does / what it does NOT do.

## Cross-file configuration

- Config A: in `path/to/file1.php` key `xxx`
- Config B: in `path/to/file2.yaml` key `yyy`
- Env vars: `FOO_*`

## Call topology

Who calls this entity:
- [[module-a]] — for purpose X
- [[module-b]] — for purpose Y

What this entity depends on:
- [[downstream-api]]
- [[redis-session-store]]

## Constraints (not visible in code)

- Rate limit: X req/min
- Concurrency: must serialize per-session
- Error handling: retry pattern, circuit breaker threshold

## Related

- Key decisions: [[decision-xxx]]
- Design patterns: [[concept-xxx]]
- Known issues: [[gotcha-xxx]]
```

---

## type: concept

**定义**：抽象的思想/模式/方法论。去掉具体实体名称后仍保留意义。可跨项目复用。

**经验法则**：去掉所有专有名词——页面是否仍然说得通？如果是，就是 concept。

### 内容契约

必需段落：

- **适用场景** —— 何时应使用此模式？
- **核心思想** —— 本质，与语言无关
- **权衡** —— 优势、代价、不适用的场景
- **应用示例** —— 至少一个 `[[entity-xxx]]` 链接，展示在本项目中的使用位置

### 模板

```markdown
---
type: concept
tags: [<domain>, ...]
date: YYYY-MM-DD
---

# <Concept Name>

## 适用场景

When you have problem X with constraints Y.

## 核心思想

The essence of the pattern, 2-4 sentences, abstract.

## 权衡

- Advantages: ...
- Costs: ...
- Does not apply when: ...

## 应用示例

- [[xxx]] uses this to handle ...
- [[yyy]] uses this with variation: ...

## 参考资料

- Origin / inspiration (book / paper / blog), if any
```

---

## type: gotcha

**定义**：一个具体场景 + 一个具体错误 + 一个具体解决方案。具体、可复现、简短。

### 内容契约

必需段落：

- **复现** —— 如何触发该问题（条件、输入）
- **症状** —— 出了什么问题（错误信息、异常行为）
- **根因** —— 为什么会发生
- **解决方案** —— 已验证的修复方法

### 严格限制

- **页面长度 ≤ 50 行**。如果更长，说明你混合了多个 gotcha——拆分。
- 标题必须描述**具体场景**，而非泛泛主题。
  - ✅ `xhs-signature-clock-skew.md`
  - ❌ `xhs-api-issues.md`

### 模板

```markdown
---
type: gotcha
tags: [<domain>, ...]
date: YYYY-MM-DD
severity: low | medium | high | critical
---

# <Specific scenario>

## 复现

1. Setup: ...
2. Action: ...
3. Observe: ...

## 症状

```
<error message or behavior>
```

## 根因

Technical explanation of why this happens.

## 解决方案

The verified fix. Code or config snippet.

## 相关

- [[entity-xxx]] — affected entity
- [[decision-xxx]] — if relevant
```

---

## type: decision

**定义**：架构决策记录（ADR）。重点在于**"为什么选这个而不是那个"**，而非"建了什么"。

### 内容契约

必需段落：

- **背景** —— 什么问题迫使做出决策
- **备选方案** —— 至少考虑 2 个选项
- **决策** —— 选择了什么
- **后果** —— 正面和负面结果、接受的权衡

### 模板

```markdown
---
type: decision
tags: [<domain>, ...]
date: YYYY-MM-DD
status: proposed | accepted | superseded | deprecated
---

# <Decision title: "Use X for Y">

## 背景

What forced this decision? What constraints applied?

## 备选方案

### 方案 A: <name>
- How it works: ...
- Pros: ...
- Cons: ...
- **否决原因**: ...

### 方案 B: <name>
- ...
- **采纳原因**: ...

### 方案 C: <name> (if any)
- ...

## 决策

Option B.

## 后果

- ✅ 正面结果
- ⚠️ 接受的权衡
- 🔄 未来重新审视的触发条件（什么会让我们重新考虑）

## 相关

- Implemented in: [[entity-xxx]]
- Design pattern: [[concept-xxx]]
- Replaces: [[decision-yyy]] (if applicable)
```

---

## type: source

**定义**：外部原始资料（官方文档、论文、博客文章、规范）的摘要页面。

**这是唯一使用文件名前缀的页面类型**：`source-<name>.md`。

> **如果 source 需要从 URL 获取**（用户粘贴 URL 并要求直接摄入，绕过 research），在构建摘要之前，遵循 [`../../research/references/data-collection.md`](../../research/references/data-collection.md) 中的工具矩阵和完整性规则。简单的 `curl`-然后放弃方法会用不完整数据损坏 source 页面；当获取复杂度较高时，优先通过 `research` skill 路由处理。

### 内容契约

- source 涵盖内容的简要摘要（2-4 段）
- 适用于本项目的关键要点
- 原始 source 链接
- 本 source 影响的相关 entity/concept 页面链接

### 模板

```markdown
---
type: source
tags: [<domain>, <source-type>]
date: YYYY-MM-DD
origin: <URL or citation>
---

# <Source Title>

> Original: <URL>
> Accessed: YYYY-MM-DD

## 摘要

2-4 paragraphs of what the source covers.

## 对本项目的关键要点

- Point 1 that applies to us
- Point 2 that applies to us

## 关联页面

- [[entity-xxx]] — how this source shaped the entity
- [[concept-xxx]] — abstract pattern derived from this source
```

---

## 类型决策树（摄入时使用）

当用户要求摄入时，使用此决策树分类：

1. 是**外部原始资料**（文档/论文/博客）？→ `source`
2. 是**具体场景 + 错误 + 修复方案**？→ `gotcha`
3. 是**选择某个方案而非其他方案的理由**？→ `decision`
4. **去掉专有名词后仍然说得通**？→ `concept`
5. 是**本项目中的真实对象**（API、模块、表、队列）？→ `entity`

如果模糊，优先选择更具体的类型（gotcha > decision > entity > concept），使其携带更多约束信号。
