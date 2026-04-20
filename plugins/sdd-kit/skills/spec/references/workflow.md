# Spec 工作流：Frame / Decide / Finalize

三个原语的详细流程。SKILL.md 给出高层步骤；本文件给出包含边界情况的完整工作流。

---

## Frame

在填充内部内容之前，先确立 spec 的外廓。

### 触发短语

- "写 spec X" / "开始 spec X" / "spec 一下 X"
- "定方案 X" / "设计 X 的实现方案"
- "draft the spec for X" / "let's spec X"

### 完整流程

**步骤 1 — 命名 spec**

从用户表述中提取主题。转换为 kebab-case 格式，以主题命名：

- ✅ `xhs-customer-webhook.md`, `user-export-api.md`, `rate-limit-refactor.md`
- ❌ `feature-xhs.md`, `2025-04-xhs-webhook.md`, `v2-webhook.md`

检查 `.claude/specs/<name>.md` 是否已存在：

- 存在且 `status: accepted` → 询问："spec `<name>` 已存在（status=accepted）。要 (a) 修订现有, (b) 开新版本移旧到 archive/, (c) 取消？"
- 存在且 `status: draft` → "spec `<name>` 草稿已存在，继续当前草稿？"

**步骤 2 — 可选：消费 research 成果**

如果用户引用了 research："基于 research/<topic>/findings.md 写 spec" 或类似表述：

1. 读取 `.claude/research/<topic>/findings.md`
2. 提取：关键发现（作为 spec 背景信息）、开放问题（作为 Decide 步骤的输入）、约束条件（写入 Constraints 章节）
3. **禁止逐字复制 research 内容**。Research 是探索叙述；spec 是最终结论。

如果用户未引用 research：仅根据用户在会话中的输入推进。

**步骤 3 — 可选：参考 wiki**

如果用户说"参考 wiki 里的 X"，或主题明显有先前经验可借鉴：

1. 调用 wiki Query 原语（只读）——参见 wiki skill
2. 将相关决策/实体/注意事项以**背景上下文**的形式融入 spec，使用 `[[wikilink]]` 引用
3. 禁止将 wiki 内容复制到 spec 中——用链接代替

**步骤 4 — 撰写骨架**

从 [../assets/templates/spec.md](../assets/templates/spec.md) 加载模板。填写：

- Frontmatter：`status: draft`、`date`、可选的 `tags`
- `# <Feature>`
- **Goal** — 一句话，祈使语气
- **Non-goals** — 至少 2 条明确的排除项
- **Hard constraints** — 尽可能使用数值

其余章节保留为 `<TODO: ...>` 占位符。

**步骤 5 — 与用户确认骨架**

输出：

```
📝 .claude/specs/<name>.md (status=draft)
   Goal: <one sentence>
   Non-goals: <N items>
   Constraints: <N items>

确认骨架无误再进入 Decide 阶段？
```

等待用户确认后再填充内部内容。

### 边界情况

**情况：用户想写 spec 但目标不清晰**

提出一个有针对性的问题。"这个 spec 要回答的核心问题是什么？是新建功能，还是替换现有实现，还是扩展接口？"

**情况：non-goals 章节为空**

质疑用户。没有 non-goals 的 spec 必然会范围蔓延。给出示例："要不要明确写明：此 spec 不涉及 X / Y？"

---

## Decide

逐一解决开放问题。将结论记录为平铺陈述。

### 触发条件

在草稿阶段，当某个章节出现 `<TODO-DECIDE: ...>` 或用户提出开放问题时。

### 完整流程

**步骤 1 — 列举开放问题**

来源：research.findings.open-questions + 会话中新浮现的问题 + 骨架中的 `<TODO-DECIDE>` 标记。先全部列出，再逐一解决。

示例：

```
📋 Open questions:
  1. 签名算法: HMAC-SHA256 vs RSA-SHA256
  2. 重试策略: 指数回退 vs 固定间隔
  3. 幂等 key 作用域: 按 event_id vs 按 (user_id, event_type)
```

**步骤 2 — 逐个决策**

禁止让用户一次性解决所有问题。逐个推进：

```
决策 1/3: 签名算法

选项:
(a) HMAC-SHA256 — 对称密钥，配置简单，性能高
(b) RSA-SHA256 — 非对称，可分发公钥验证，运维成本高
(c) 其他: 请说明

你的选择？
```

**步骤 3 — 记录为平铺陈述**

用户做出选择后，写入 spec：

- ✅ `Signature: HMAC-SHA256. Secret rotated via KMS every 90 days.`
- ❌ `We considered HMAC-SHA256 vs RSA-SHA256. Chose HMAC because...`

Spec 记录结论，不记录过程。

**步骤 4 — 建议写入决策页**

每次非平凡决策后，建议：

```
💡 这个决策（`签名算法 = HMAC-SHA256`）有明确的取舍背景。要不要把来龙去脉 ingest 为 wiki:
   - type: decision
   - name: hmac-vs-rsa-for-xhs-webhook.md

这样 spec 保持干净，同时决策史得以保留。(y/n/稍后)
```

如果用户同意 → 调用 wiki `ingest` 原语。
如果用户拒绝或选择稍后 → 从 spec 中移除理由，不在 spec 本身保留。

**步骤 5 — 更新 spec 章节**

用平铺陈述替换 `<TODO-DECIDE>`。继续处理下一个开放问题。

### 边界情况

**情况：用户说"你定"**

禁止默默选择。先陈述建议和核心理由，再请求确认：

```
我的建议: HMAC-SHA256 (理由: 本项目已有 KMS，对称密钥运维成本低)
确认吗？(y/n/改别的)
```

只有用户确认后才写入。

**情况：用户提出了菜单之外的第三个选项**

欣然接受。将新选项记录为决策。

**情况：决策暂时无法做出（缺少信息）**

保留 `<TODO-DECIDE: ...>` 标记。在 Finalize 阶段，此标记会阻止定稿并给出明确提示。禁止静默移除。

---

## Finalize

封印 spec。此文档不再允许修改，除非启动新一轮修订。

### 触发短语

- "spec 定稿" / "finalize"
- "这份 spec 可以了"
- "confirm the spec"

### 完整流程

**步骤 1 — 扫描未解决的标记**

```bash
grep -n "TODO-DECIDE\|<TBD>\|<?>" .claude/specs/<name>.md
```

如有匹配 → 阻止定稿：

```
❌ 还有未解决项:
   - line 42: TODO-DECIDE: retry policy
   - line 67: <TBD>: idempotency scope

请先完成 Decide 再 finalize。
```

**步骤 2 — 执行内容契约检查**

完整清单参见 [content-contract.md](content-contract.md)。自动化扫描：

```bash
# 检查叙述性内容 / 备选方案 / 历史记录标记
grep -nE "^(## (Alternatives|Rejected|History|Rationale|Why we chose))" .claude/specs/<name>.md
grep -nE "(we considered|we first thought|we decided against|originally we)" .claude/specs/<name>.md
```

如发现 → 阻止定稿，建议移至 `[[decision-*]]` wiki 页面。

**步骤 3 — 检查 Goal / Non-goals 覆盖度**

- Goal 章节不为空，不含抽象形容词（"good"、"fast"、"solid"）
- Non-goals 章节至少有 2 条明确条目
- Constraints 章节包含可量化的值（延迟、吞吐量、一致性级别等）

如有不满足 → 输出具体修正建议，禁止自动改写。

**步骤 4 — 设置 frontmatter**

```yaml
---
status: accepted
date: YYYY-MM-DD
<other fields preserved>
---
```

**步骤 5 — 输出结稿摘要**

```
✅ spec 定稿: .claude/specs/<name>.md (status=accepted)

Sections present: Goal, Non-goals, Constraints, Interface, Data/State, Integration, Test strategy
Decision-pages created: N (if any were ingested)
Open items: 0

下一步建议 (用户决定):
- 运行 task skill 把 spec 拆成原子任务
- 或者直接运行 impl (若 spec 足够小可以不拆)
- 或者暂不推进，把 spec 交给他人 review
```

### 边界情况

**情况：用户想在 accept 之后重新打开 spec**

允许。将 `status` 设为 `revising`，修改内容后重新执行 Finalize。修订历史由 git 追踪，不记录在 spec 内部。

**情况：spec 取代了之前的版本**

在 frontmatter 中写入：`supersedes: <old-spec-name>`。在旧 spec 中写入：`status: superseded`、`superseded-by: <new-spec-name>`。可选：将旧 spec 移至 `archive/`。

**情况：spec 过长（> 400 行）**

警告："spec 长度 N 行，通常 ≤ 300 行为宜。是否可以拆成 2 个 spec（e.g. interface + internals）？"
