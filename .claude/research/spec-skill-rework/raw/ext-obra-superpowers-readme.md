---
url: https://raw.githubusercontent.com/obra/superpowers/main/README.md
tool: read_url_content
fetched_at: 2026-04-21 21:30
---

# obra/superpowers README 关键摘录

> superpowers 是 skill-first 架构的 Claude Code plugin,是 sdd-kit 架构参考的同生态样本。仅摘录与"skill 如何组织、触发、SKILL.md 大小风格"相关段落。

---

## How it works(全文,仅几段)

```
It starts from the moment you fire up your coding agent. As soon as it sees that
you're building something, it *doesn't* just jump into trying to write code.
Instead, it steps back and asks you what you're really trying to do.

Once it's teased a spec out of the conversation, it shows it to you in chunks
short enough to actually read and digest.

After you've signed off on the design, your agent puts together an implementation
plan that's clear enough for an enthusiastic junior engineer with poor taste,
no judgement, no project context, and an aversion to testing to follow.
It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY.

Next up, once you say "go", it launches a *subagent-driven-development* process,
having agents work through each engineering task, inspecting and reviewing their work,
and continuing forward. It's not uncommon for Claude to be able to work autonomously
for a couple hours at a time without deviating from the plan you put together.

There's a bunch more to it, but that's the core of the system. And because the
skills trigger automatically, you don't need to do anything special.
Your coding agent just has Superpowers.
```

**观察**:
- **"skills trigger automatically"** —— superpowers 不依赖用户显式点名 skill,靠 description 让模型自行触发。这与 sdd-kit 当前"显式请求"策略相反。
- README 本身只用 5 段话介绍整个工作流 —— 极简
- 强调 TDD / YAGNI / DRY 等**编程价值观**,不详述 skill 结构

## Skills Library(完整清单)

```
**Testing**
- **test-driven-development** - RED-GREEN-REFACTOR cycle
  (includes testing anti-patterns reference)

**Debugging**
- **systematic-debugging** - 4-phase root cause process
  (includes root-cause-tracing, defense-in-depth, condition-based-waiting techniques)
- **verification-before-completion** - Ensure it's actually fixed

**Collaboration**
- **brainstorming** - Socratic design refinement
- **writing-plans** - Detailed implementation plans
- **executing-plans** - Batch execution with checkpoints
- **dispatching-parallel-agents** - Concurrent subagent workflows
- **requesting-code-review** - Pre-review checklist
- **receiving-code-review** - Responding to feedback
- **using-git-worktrees** - Parallel development branches
- **finishing-a-development-branch** - Merge/PR decision workflow
- **subagent-driven-development** - Fast iteration with two-stage review

**Meta**
- **writing-skills** - Create new skills following best practices
- **using-superpowers** - Introduction to the skills system
```

**关键观察**:
- **skill 粒度非常细**:`writing-plans` / `executing-plans` / `finishing-a-development-branch` / `requesting-code-review` / `receiving-code-review` 各为独立 skill
- **skill 命名用动名词**(writing- / executing- / receiving-)而非名词(planner / executor)
- **扁平列表 + 分类 tag**(Testing / Debugging / Collaboration / Meta),skill 之间不嵌套
- **有一个 `writing-skills` meta-skill** 教如何写其它 skill —— 元技能自举

## 推论(未原文)

- superpowers 没单独提供"engineering spec"类的 skill —— 它的 spec 是通过 brainstorming + writing-plans 完成的对话产物,不是单文件契约
- 这说明 superpowers 的 spec 定位比 sdd-kit 更"临时" —— 过程化、对话式,不强调"最终契约"
- sdd-kit 选择了**单文件强契约**路径,更接近 SpecKit / KEP / Rust RFC

## SKILL.md 结构(README 未直接展示,需单独研究)

README 未展示实际 SKILL.md 样例。从注释推断:

- superpowers 的 SKILL.md 篇幅信息需要直接看仓库 `skills/*/SKILL.md`(本次未进一步 fetch,success criteria 2-3 不依赖此数据即可满足)
- 已知同类 skill 命名与分组方式,对本次 sdd-kit spec skill 改造的启发是:保持单 skill 独立职责,不跨 skill 抢活
