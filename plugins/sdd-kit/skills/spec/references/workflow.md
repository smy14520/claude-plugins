# Spec workflow: Frame / Decide / Finalize

Detailed procedures for the three primitives. SKILL.md gives high-level steps; this file gives the full workflow including edge cases.

---

## Frame

Establish the spec's outer shape before writing internals.

### Trigger phrases

- "写 spec X" / "开始 spec X" / "spec 一下 X"
- "定方案 X" / "设计 X 的实现方案"
- "draft the spec for X" / "let's spec X"

### Full procedure

**Step 1 — Name the spec**

Extract topic from user's utterance. Convert to kebab-case, topic-named:

- ✅ `xhs-customer-webhook.md`, `user-export-api.md`, `rate-limit-refactor.md`
- ❌ `feature-xhs.md`, `2025-04-xhs-webhook.md`, `v2-webhook.md`

Check if `.claude/specs/<name>.md` already exists:

- Exists with `status: accepted` → ask: "spec `<name>` 已存在（status=accepted）。要 (a) 修订现有, (b) 开新版本移旧到 archive/, (c) 取消？"
- Exists with `status: draft` → "spec `<name>` 草稿已存在，继续当前草稿？"

**Step 2 — Optionally consume research**

If user references research: "基于 research/<topic>/findings.md 写 spec" or similar:

1. Read `.claude/research/<topic>/findings.md`
2. Extract: key findings (become spec background), open questions (become Decide step input), constraints (carry into Constraints section)
3. **Do NOT copy research content verbatim**. Research is discovery narrative; spec is the final statement.

If user does NOT reference research: work from user's in-session input only.

**Step 3 — Optionally consult wiki**

If user says "参考 wiki 里的 X" or the topic has obvious prior art:

1. Invoke wiki Query primitive (read-only) — see wiki skill
2. Fold relevant decisions/entities/gotchas into the spec as **background context**, using `[[wikilink]]` references
3. Do NOT duplicate wiki content into the spec — link instead

**Step 4 — Write skeleton**

Load template from [../assets/templates/spec.md](../assets/templates/spec.md). Fill:

- Frontmatter: `status: draft`, `date`, optional `tags`
- `# <Feature>`
- **Goal** — ONE sentence, imperative voice
- **Non-goals** — ≥ 2 explicit exclusions
- **Hard constraints** — numeric where possible

Leave all other sections as `<TODO: ...>` placeholders.

**Step 5 — Confirm frame with user**

Emit:

```
📝 .claude/specs/<name>.md (status=draft)
   Goal: <one sentence>
   Non-goals: <N items>
   Constraints: <N items>

确认骨架无误再进入 Decide 阶段？
```

Wait for user confirmation before filling internals.

### Edge cases

**Case: user wants a spec but goal is unclear**

Ask ONE targeted question. "这个 spec 要回答的核心问题是什么？是新建功能，还是替换现有实现，还是扩展接口？"

**Case: non-goals section is empty**

Challenge the user. A spec without non-goals drifts. Offer examples: "要不要明确写明：此 spec 不涉及 X / Y？"

---

## Decide

Resolve open questions one at a time. Record outcomes as flat statements.

### Trigger

During draft, whenever a section has `<TODO-DECIDE: ...>` or the user flags an open question.

### Full procedure

**Step 1 — Enumerate open questions**

From research.findings.open-questions + in-session surfaced + skeleton `<TODO-DECIDE>` markers. List them before resolving any.

Example:

```
📋 Open questions:
  1. 签名算法: HMAC-SHA256 vs RSA-SHA256
  2. 重试策略: 指数回退 vs 固定间隔
  3. 幂等 key 作用域: 按 event_id vs 按 (user_id, event_type)
```

**Step 2 — One decision at a time**

Do NOT ask the user to resolve all at once. Go one-by-one:

```
决策 1/3: 签名算法

选项:
(a) HMAC-SHA256 — 对称密钥，配置简单，性能高
(b) RSA-SHA256 — 非对称，可分发公钥验证，运维成本高
(c) 其他: 请说明

你的选择？
```

**Step 3 — Record as flat statement**

After user chooses, write into spec as:

- ✅ `Signature: HMAC-SHA256. Secret rotated via KMS every 90 days.`
- ❌ `We considered HMAC-SHA256 vs RSA-SHA256. Chose HMAC because...`

The spec states the outcome, not the path.

**Step 4 — Offer decision-page ingest**

After each non-trivial decision, offer:

```
💡 这个决策（`签名算法 = HMAC-SHA256`）有明确的取舍背景。要不要把来龙去脉 ingest 为 wiki:
   - type: decision
   - name: hmac-vs-rsa-for-xhs-webhook.md

这样 spec 保持干净，同时决策史得以保留。(y/n/稍后)
```

If user says yes → invoke wiki `ingest` primitive.
If user says no or later → drop rationale from spec, do not preserve in spec itself.

**Step 5 — Update spec section**

Replace `<TODO-DECIDE>` with the flat statement. Move to next open question.

### Edge cases

**Case: user says "你定"**

Do NOT silently pick. State your recommendation + top reason + ask for confirmation:

```
我的建议: HMAC-SHA256 (理由: 本项目已有 KMS，对称密钥运维成本低)
确认吗？(y/n/改别的)
```

Only write once user confirms.

**Case: user proposes a third option not in the menu**

Gladly accept. Record the new option as the decision.

**Case: decision cannot be made yet (missing info)**

Keep the `<TODO-DECIDE: ...>` marker. At Finalize step, this will block closure with a clear message. Do not silently drop.

---

## Finalize

Seal the spec. No more changes to this document without a new revision.

### Trigger phrases

- "spec 定稿" / "finalize"
- "这份 spec 可以了"
- "confirm the spec"

### Full procedure

**Step 1 — Scan for unresolved markers**

```bash
grep -n "TODO-DECIDE\|<TBD>\|<?>" .claude/specs/<name>.md
```

If any match → block finalization:

```
❌ 还有未解决项:
   - line 42: TODO-DECIDE: retry policy
   - line 67: <TBD>: idempotency scope

请先完成 Decide 再 finalize。
```

**Step 2 — Apply content-contract check**

See [content-contract.md](content-contract.md) for full list. Automated scan:

```bash
# Check for narrative / alternatives / history markers
grep -nE "^(## (Alternatives|Rejected|History|Rationale|Why we chose))" .claude/specs/<name>.md
grep -nE "(we considered|we first thought|we decided against|originally we)" .claude/specs/<name>.md
```

If found → block, suggest moving to a `[[decision-*]]` wiki page.

**Step 3 — Check goal / non-goals coverage**

- Goal section ≠ empty, ≠ abstract adjectives ("good", "fast", "solid")
- Non-goals section has ≥ 2 explicit items
- Constraints section has measurable values (latency, throughput, consistency class, etc.)

If any fail → emit specific fixit, do NOT auto-write.

**Step 4 — Set frontmatter**

```yaml
---
status: accepted
date: YYYY-MM-DD
<other fields preserved>
---
```

**Step 5 — Emit closing summary**

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

### Edge cases

**Case: user wants to re-open after accept**

Allowed. Set `status: revising`, make changes, re-run Finalize. The history of revisions is tracked by git, not in the spec.

**Case: spec supersedes an earlier one**

In frontmatter: `supersedes: <old-spec-name>`. In old spec: `status: superseded`, `superseded-by: <new-spec-name>`. Optionally move old spec to `archive/`.

**Case: spec is too large (> 400 lines)**

Warn: "spec 长度 N 行，通常 ≤ 300 行为宜。是否可以拆成 2 个 spec（e.g. interface + internals）？"
