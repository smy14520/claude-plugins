# 维护规则 R1–R5

五条防止 wiki 腐化的规则。R1 和 R4 是自动执行的；R2、R3、R5 是建议性的（由用户决定）。

---

## R1 —— 摄入时根页面自动更新

**触发条件**：每次摄入新页面时。

**操作**：

1. 读取新页面的 `tags:` frontmatter
2. 找到 tags 与新页面重叠的根页面
3. 对每个匹配的根页面：
   - 在根页面最合适的段落中插入 wikilink
   - 如果变更是重大变更，在根页面的 `版本演进` 段落中追加一行

**段落映射规则**（新页面类型 → 根页面段落）：

| 新页面类型 | 应更新的根页面段落 |
|------|------|
| `entity`（与 `root` 标签重叠） | 核心模块 或 已接入渠道（取适合领域的） |
| `entity`（基础模块） | 基础设施 |
| `concept` | 设计模式 |
| `decision` | 关键决策 |
| `gotcha` | 已知陷阱 |
| `source` | 外部资料 |

**当段落不适用于根页面时**（例如根页面没有已接入渠道段落，因为它不是多渠道系统）：添加该段落，或选择最接近的现有段落。不要静默跳过。

**关于"重大性"的判断**：

以下情况更新版本演进：
- 新增渠道/供应商/后端（面向用户的变更）
- 重大决策改变了架构
- 不需要为每个常规 gotcha/次要 concept 更新

### 示例

摄入：`xhs-api.md`，`tags: [xhs, api, external, customer-service]`。

匹配的根页面：`ai-customer-service.md`（包含标签 `customer-service`）。

操作：
1. 在 `ai-customer-service.md` 的 `## 已接入渠道` 段落下插入 `- [[xhs-api]]`
2. 在版本演进中追加：`- YYYY-MM: 接入小红书（[[spec-xhs-customer-channel]]）`

---

## R2 —— index.md 排除列表

**触发条件**：每次修改 `index.md` 时。

**规则**：`index.md` 不得包含以下引用：

- 任何根页面的子页面（例如 `xhs-api`——归属于 `ai-customer-service.md`）
- 非跨域的概念/决策（归属于其根页面的对应段落）
- 非跨域的 gotcha（归属于其根页面的已知陷阱）

**index.md 仅可包含以下引用**：

- 带 `tags: [root]` 的页面
- 带 `tags: [cross-domain]` 的页面
- 名为 `source-*.md` 的页面（source 摘要）
- 孤立页面（由 lint 自动维护，见 R4）

**执行方式**：当 index.md 包含违反 R2 的页面引用时，lint 会发出警告。该页面应：
- 从 index.md 中移除（因为它已归属于某个根页面），或
- 如果它确实是跨系统的，添加 `cross-domain` 标签，或
- 如果它应该是领域枢纽，升级为 `root`

---

## R3 —— 根页面晋升建议

**触发条件**：在摄入或 lint 期间。

**检测条件**：非根页面 `P` 被 ≥ 5 个其他页面引用。

**操作**：不要自动晋升。改为发出建议：

```
💡 R3 suggestion: [[P]] is referenced by N pages. Consider promoting it to a root page.
Promotion procedure:
  1. Add `root` to P's frontmatter tags
  2. Restructure P's content to match the root page template
     (see references/index-and-root.md#root-page-template)
  3. Add P to index.md's 🏠 根实体 section
```

**理由**：自动晋升可能重构一个用户不想重构的页面。将此决定权留给用户。

**降级**（反向 R3）：未实现。如果页面已晋升为根页面但不再需要（罕见），用户手动移除 `root` 标签并更新 index.md。

---

## R4 —— 孤立页面检测与 index 同步

**触发条件**：每次 lint 运行，以及每次摄入（简化版：仅检查新摄入的页面）。

**检测条件**：

- 页面 `P` 是孤立页面，当：
  - `P` 不是根页面（没有 `tags: [root]`）
  - `P` 不是 `source-*.md`
  - `.claude/wiki/` 中没有其他页面包含 `[[P]]`

**操作**：

1. 维护 `index.md` 中的 ⚠️ 孤立页面段落：
   - 如果新出现孤立页面，将 `P` 添加到孤立列表
   - 如果 `P` 被链接了，将其从孤立列表中移除
2. 不要修改 index.md 的其他段落

**理由**：孤立页面反映 wiki 健康度。零孤立 = 组织紧密。大量孤立 = 需要整理。

**阈值警报**（仅 lint）：

```
If orphan_count / total_non_root_pages > 0.3:
  emit strong warning: "Wiki 组织可能失控，考虑整理或升级 root"
```

---

## R5 —— 新鲜度信号（按年龄标记）

**触发条件**：在 `Query` 过程中（内联，逐页）和 `Lint` 过程中（批量报告）。

**理由**：GitHub Copilot 2026 年 1 月的工程文章关于记忆质量指出：

> "记忆质量主要是一个新鲜度和失效问题——**过时的、分支特定的记忆往往比没有记忆更危险**。"

一个写着"我们在去年 Q2 决定了 X"的页面，只有在读者知道其年龄时才可操作。隐藏年龄 = 无声腐败风险。

**决策：展示年龄，不自动失效。**

- 不将 wiki 页面与源代码 mtime 绑定（误报风险高，维护负担大）。
- 不自动删除或降级旧页面（需要用户判断）。
- 确实将逐页年龄作为中性信号展示，并将 > 180 天标记为"审查候选"。

**阈值**（基于页面的最后修改时间，或 `date:` frontmatter（如果存在））：

| 年龄区间 | Query 输出 | Lint 分类 |
|-----------|-------------|---------------------|
| < 90 天 | 无标注 | 不标记 |
| 90–180 天 | 轻微提示（可选，例如 `(3 months ago)`） | 不标记 |
| 180–365 天 | `(X months ago ⚠️)` | ⚠️ 审查候选 |
| > 365 天 | `(X months ago ⚠️ stale)` | ⚠️ 审查候选（强） |

**操作**（仅 Lint，在批量报告中）：

```
⚠️ Review candidates (age-based, not broken — review and decide):
- [[decision-hmac-algo]]   8 months ago
- [[entity-old-crm]]       1 year ago (strong)
```

用户逐案决定是否：
1. 保持不动（仍然有效，只是旧的）
2. 重新验证内容并更新 `date:` frontmatter（刷新）
3. 标记为已过时，添加 `deprecated: true` frontmatter（软删除）
4. 删除（硬删除）

**R5 豁免**：
- `source-*.md` 页面（外部文档本身就有时间戳，无需标记）
- 带 `tags: [evergreen]` 的页面（显式退出，用于不会过时的稳定模式）

**禁止事项**：
- 在 Query 输出中静默移除旧页面（用户必须看到它们才能做决定）
- 不重新阅读页面就自动更新 `date:` frontmatter（违背整个信号机制）
- 将 R5 标记视为阻断性错误（它们是信号，不是故障）

### 示例：带 R5 的 Query 输出

```
📚 Wiki Query: "xhs webhook 签名"

### 已读取
- [[xhs-api]]                          (2 weeks ago)
- [[xhs-signature-clock-skew]]         (3 months ago)
- [[decision-hmac-algo]]               (8 months ago ⚠️)
- [[idempotent-webhook]]               (1 year ago ⚠️ stale)
```

### 示例：带 R5 的 Lint 输出

```
❌ Real issues:
  - [[foo]] broken link to [[missing-page]]
  - [[bar]] orphan (no incoming links)

⚠️ Review candidates (age-based):
  - [[decision-hmac-algo]]   8 months ago
  - [[idempotent-webhook]]   1 year ago (strong)
```

严重程度视觉区分：❌ = "已损坏，需修复"；⚠️ = "检查是否仍然准确"。

---

## 规则间的交互关系

- **R1 和 R4 互补**：R1 确保新页面被根页面链接，从而防止它们成为孤立页面。如果 R1 失败（未找到匹配的根页面），R4 会将该页面捕获为孤立页面。
- **R2 和 R4 紧密耦合**：R4 更新 index.md 的孤立段落，而 R2 明确允许（这是 index.md 列出非根/非跨域页面的唯一情况）。
- **R3 独立**：它是一个用户提示，可以在任何操作过程中出现。
- **R5 与 R1-R4 正交**：新鲜度与链接关系是分离的。一个链接良好的页面可能已过时；一个孤立页面可能仍然新鲜。Lint 在不同段落中报告它们。

---

## 失败模式与恢复

### R1 失败：摄入的页面不匹配任何根页面

页面自动成为孤立页面（R4 会捕获）。无错误。下次摄入或 lint 会揭示孤立状态，用户可以：
- 创建匹配的根页面
- 为页面添加 `cross-domain` 标签（如果合适）
- 暂时保留为孤立页面

### R2 违规：有人将子页面添加到了 index.md

Lint 检测并警告。用户手动从 index.md 中移除。不自动修复，因为移除可能是有意的（例如子页面被晋升为 `cross-domain`）。

### R1 重复更新：重新摄入同一页面

在根页面中插入 wikilink 之前，检查 wikilink 是否已存在。如果已存在，跳过插入，但如果存在语义变更仍然更新版本演进。

---

## 测试（为将来的 TDD 准备）

实现这些规则的自动化时，以下行为应有回归测试：

1. **R1 基本场景**：摄入 `xhs-api.md`（带标签 `customer-service`）→ `ai-customer-service.md` 在已接入渠道中获得 `[[xhs-api]]`
2. **R1 无根页面**：摄入 `foo.md`（标签无任何根页面匹配）→ 页面为孤立，index.md 孤立段落已更新
3. **R1 多根页面**：摄入时标签匹配 2 个根页面 → 提示用户（或选择最大重叠）
4. **R2 违规**：手动将 `[[xhs-api]]` 添加到 index.md → lint 标记
5. **R3 建议**：创建 5 个页面都链接到 `[[foo]]` → lint 建议晋升 `foo`
6. **R4 孤立循环**：创建孤立页面 → 被另一页面链接 → 孤立段落清除
7. **R5 query 年龄**：Query 触及 > 180 天的页面 → 输出包含 `⚠️` 年龄标注
8. **R5 lint 候选**：对混合新鲜/过时页面的 wiki 执行 lint → 过时页面出现在 `Review candidates` 段落，而非 `Real issues` 段落
9. **R5 evergreen 豁免**：带 `tags: [evergreen]` 的页面年龄 > 1 年 → lint 不标记
10. **R5 source 排除**：`source-*.md` 年龄 > 1 年 → 不标记
