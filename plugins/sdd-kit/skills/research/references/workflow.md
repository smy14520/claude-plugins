# Research workflow: Scope / Collect / Refine / Propose

Detailed procedures for the four primitives. SKILL.md gives high-level steps; this file gives the full workflow including edge cases.

---

## Scope

Frame the question before touching any material. A research without a declared scope becomes an infinite browse.

### Trigger phrases

- "研究一下 X" / "调研 X"
- "想做 X 先探索"
- "X 之前有人做过吗，看看"
- "do research on X" / "explore X"

### Full procedure

**Step 1 — Extract the topic**

From the user's utterance, pull out:

- Topic name (one noun phrase) → becomes `<topic>` directory in kebab-case
- Feeding decision (what choice is this research going to feed?)

If the feeding decision is unclear, ask ONE question: "这个研究的结论会影响什么决策？是想选型、估工、还是理解现有代码？"

**Step 2 — Write `question.md`**

Load template from [../assets/templates/question.md](../assets/templates/question.md). Fill:

- **Question**: single sentence
- **In scope**: 2-4 bullets, concrete sub-questions
- **Out of scope**: 2+ bullets, explicit exclusions (critical — this is what prevents bloat)
- **Feeding decision**: what spec/task will consume this
- **Time budget**: user's rough estimate (optional, but helpful)

**Step 3 — Emit summary**

```
📁 .claude/research/<topic>/question.md 已创建
   In scope: X, Y
   Out of scope: Z
   下一步: collect (粘贴资料 / 告诉我从哪里开始看)
```

### Edge cases

**Case: user hasn't narrowed the scope**

Do not guess. Ask ONE question: "你希望这次 research 主要回答什么？" then fill.

**Case: user's scope is huge (e.g. "研究一下前端架构")**

Propose a narrower scope: "这个范围很大。建议先限定在一个具体问题（如 '如何组织 shared UI components'），回头再扩展。OK 吗？"

---

## Collect

Gather raw material into `raw/`. Do not distill here.

### Trigger phrases

- User pastes docs, URLs, screenshots
- "看一下代码里 X 怎么做的"
- "收集 X 的资料"

### Full procedure

**Step 1 — Categorize the input**

- Pasted doc / text → `raw/user-input-YYYY-MM-DD.md`
- URL → fetch, summarize briefly (NOT distill), save as `raw/ext-<slug>.md`
- Code read request → scan, save relevant quotes with file:line refs as `raw/codebase-<area>.md`

**Step 2 — Write raw file with minimal structure**

Each raw file has:

```markdown
# <Title>

> Source: <URL | path | user>
> Collected: YYYY-MM-DD

## Content

<verbatim or near-verbatim excerpt>
```

**Step 3 — Do NOT distill during collect**

Temptation: while reading code, you see a pattern and want to write "this is using pattern X". Resist. Put the excerpt in `raw/`; the refine step will decide whether to abstract.

**Step 4 — Track what's been collected**

After each collect action, emit:

```
📥 Collected: raw/<file>.md
   已有 raw 文件: N 个
   建议: 继续收集 / 开始 refine
```

### Edge cases

**Case: user provides a very long URL / document**

Do not fetch entire doc. Fetch + summarize to ≤ 200 lines, noting what was omitted. Keep original URL prominent.

**Case: scan reveals codebase has nothing relevant**

Record one-line `raw/codebase-<area>.md`: "Scanned `<paths>`, no relevant matches for `<topic>`."

**Case: user wants to skip collect and go straight to refine**

Only allowed if they are pasting already-curated material. Warn: "跳过 collect 意味着没有原始引用链路。你确定这些资料已经是提炼过的？"

---

## Refine

Distill raw material into focused `refined/<topic>.md` notes.

### Trigger phrases

- "整理一下"
- "把收集到的提炼一下"
- "refine 一下"

### Full procedure

**Step 1 — Group raw files by finding**

Read all `raw/*.md`. Group excerpts by the *finding* they support, not by their source.

Example: signatures mentioned in three different raw files → all feed one `refined/xhs-signature-scheme.md`.

**Step 2 — Write one refined note per finding**

Apply [../assets/templates/finding-note.md](../assets/templates/finding-note.md). Required sections:

- **What I found**: the concrete finding (1-3 sentences)
- **Where**: citations back to `raw/` files with line refs
- **Why it matters**: how this affects the feeding decision
- **Open question**: what is still unknown after this finding

Hard limit: ≤ 80 lines per note. Longer → split.

**Step 3 — Discard unused raw**

Raw files that didn't contribute to any refined note:

- If they might be useful later → leave them
- If they are clearly irrelevant → delete or move to `raw/.discarded/`

Never keep "just in case" raw without a clear downstream purpose.

**Step 4 — Emit refine summary**

```
🔍 Refined: N 个 refined notes
   - <finding-1> → <note-1>.md
   - <finding-2> → <note-2>.md
   未用 raw 文件: M 个 (保留 / 丢弃)
```

### Edge cases

**Case: a finding wants to become a decision**

If while refining you feel "this finding is actually our choice", STOP. Research does not decide. Rewrite as option-description:

- ❌ "We should use webhook"
- ✅ "Webhook is available. Poll is also available. Tradeoffs: ..."

**Case: a finding is too abstract to cite**

Unverified findings are not findings. Either cite or drop.

---

## Propose

Close out the research. Produce `findings.md` + wiki-ingest candidates.

### Trigger phrases

- "总结一下 research"
- "research 完了"
- "可以结束研究了"
- "closing the research"

### Full procedure

**Step 1 — Write `findings.md`**

Apply [../assets/templates/findings.md](../assets/templates/findings.md). Required sections:

- **Question** (copy from question.md)
- **Key findings** (≤ 7 bullets, each linking a `refined/` note)
- **Open questions** (for spec to resolve — explicit list, can be empty only if truly no open Q)
- **Ingest candidates** — which refined notes are worth promoting to wiki
- **Ephemeral** — which refined notes are scoped to this decision only (will not be ingested)

**Step 2 — Classify ingest candidates by proposed wiki type**

For each candidate, suggest the wiki page type (per wiki skill):

- `entity` — if it describes a real object in the project
- `concept` — if it is a reusable abstraction
- `gotcha` — if it is a specific scenario + error + fix
- `decision` — if it captures a choice and rationale (will usually become a decision page AFTER spec, not during research)
- `source` — if it is a summary of external raw material

**Step 3 — Do NOT auto-ingest**

Explicitly instruct the user:

> 以上 ingest 建议仅为提议。若要真正写入 wiki，请调用 `wiki` skill 并 ingest 具体条目。

**Step 4 — Emit closing summary**

```
📤 Research closed: .claude/research/<topic>/findings.md

Key findings: N
Open questions: M
Ingest candidates: K (entity: A, concept: B, gotcha: C)

下一步建议 (用户决定):
- 运行 spec skill 起草方案（open questions 会成为决策点）
- 运行 wiki ingest 沉淀 ingest 候选
- 或两者都做，按顺序由你决定
```

### Edge cases

**Case: open questions list is empty**

Challenge: "研究结束但没有 open question，是研究确实彻底，还是实际上没发散？" Let user confirm before closing.

**Case: ingest candidates list is empty**

Fine — not every research produces reusable knowledge. Note in findings.md: "本次 research 无 wiki ingest 候选（所有发现均为本次决策 scoped）。"

**Case: user wants to revisit / extend later**

Leave `findings.md` with `status: open` in frontmatter. A future session can append without rewriting.
