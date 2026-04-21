# sdd-kit

**SDD Kit** — Spec-Driven Development + Persistent Wiki Knowledge Layer

新一代 SDD 工具包。基于对 [autolearn-sdd-kit](../autolearn-sdd-kit) 的反思、[Karpathy LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的持久化知识模式、[superpowers](https://github.com/obra/superpowers) 的 skill-first 路线、[claude-code-configs/spf](https://github.com/fantasticcos/claude-code-configs) 的编排经验构建。

## 设计原则

1. **少即是多**：上下文精而少，不追求"完整覆盖"
2. **可控优先**：阶段之间无强制跳转，由用户显式决定
3. **知识复利**：跨需求可复用的资产沉淀到 wiki
4. **不重复代码能说的**：wiki 只写代码查不到的信息

## 五阶段流程

```
research → spec → task → impl → review
   ↖        │      │      │        │
   │        │      │      │        └─ 独立审计（读 spec + diff + wiki）
   │        │      │      └─ 自运行 acceptance（机械自检，不做语义审计）
   └────────┴──────┴──────┴────────┴──→ 用户主动 ingest → wiki（持久）
```

每阶段独立可用，文档之间**无强制跳转**。`research` 允许多轮回到同一工作区继续补资料、提问、修正理解；`spec` 则负责把已经足够收敛的理解冻结为可执行契约。`[[wikilink]]` 仅作为可选导航线索。

| 阶段 | 职责 | 产物位置 |
|------|------|---------|
| research | index-first 的需求探索工作区：发散、提问、收集资料、带来源地解释事实、逐步收敛理解，并通过 `index.md` 对外提供统一入口 | `.claude/research/<topic>/` |
| spec | 将已收敛的理解冻结为明确边界、约束与可依赖方案 | `.claude/specs/<name>.md` |
| task | 原子化执行计划（执行者不做决策） | `.claude/tasks/<name>.tasks.md` |
| impl | 按 task 执行代码实现 + 运行自己的 acceptance（SelfCheck） | 代码本身 + `## Status log` |
| review | 对照 spec + diff + wiki 做独立语义审计（4 态: APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT） | 同一 task 文件的 `## Review log` 段 |

**为什么 impl 和 review 分开？** impl 严格只看 task，无法可靠地做语义审计（会污染 "translator" 角色）。review 在新上下文里独立读 spec + `git diff` + wiki,才能真正交叉验证。详见 [skills/review/SKILL.md](./skills/review/SKILL.md)。

## Wiki 持久化层

```
.claude/wiki/
├── index.md          # 全局索引（只列 root + 跨域 + 孤立 + source）
├── log.md            # 追加式操作日志
├── <root-topic>.md   # root 页面：领域入口，带 tags: [root]
├── <topic>.md        # 子页面：主题即文件名，无类型前缀
└── source-<name>.md  # 原始资料摘要（唯一带前缀的）
```

**核心约定**：
- 文件名 = 主题名，不加类型前缀
- 类型（entity / concept / gotcha / decision / moc / source）在 frontmatter
- 子页面不入 index.md，由 root 页面承担领域导航
- 关联靠 `[[wikilinks]]` 涌现，不建 MOC 层

详见 [skills/wiki/SKILL.md](./skills/wiki/SKILL.md)。

## 当前状态

- [x] wiki skill（知识层宪法 + R1-R5 维护规则含 stale-by-age 新鲜度）
- [x] research skill（index-first 工作区 + raw 证据层 + notes 主题笔记 + log 时间线 + 可多轮续写）
- [x] spec skill（决策冻结层 + 内容契约 + 无决策史）
- [x] task skill（原子拆解 + DAG + strict-atomic/lean 双模式 + 无 wikilink）
- [x] impl skill（四态状态机 + 可验证 acceptance + 不静默决策 + 末尾 wiki-ingest 建议）
- [x] review skill（独立语义审计 + 4 态 + 读 spec/diff/wiki + 不改代码）

## 使用

**skills-only 结构**。每个 skill 是 `skills/<name>/SKILL.md`，无 `commands/` 中间层（plugin skill 本身就会被 Claude Code 注册为可直接调用的入口——多一层 commands 壳等于自己读自己，冗余且容易因相对路径产生 bug）。

触发方式:

```
自然语言（显式点名，推荐）:
  "用 research skill 调研 <topic>"
  "用 spec skill 写 <name>"
  "用 task skill 拆 <spec>"
  "用 impl skill 执行 <task-id>"
  "用 review skill 审计 <task-id>"
  "用 wiki skill ingest / query / lint <content>"

slash command（由 Claude Code 从 SKILL.md 的 name 字段自动注册）:
  /sdd-kit:research
  /sdd-kit:spec
  /sdd-kit:task
  /sdd-kit:impl
  /sdd-kit:review
  /sdd-kit:wiki
```

阶段之间**不自动跳转**。wiki 也必须显式触发。

> **防止过度触发靠什么？** **description 写严**。plugin skill 的 `disable-model-invocation` 字段 [是无效的](https://github.com/anthropics/claude-code/issues/22345)（Claude Code 已知 bug，flag 对 plugin skill 被忽略）。所有 skill 的 description 都明确写了 "Invoke only on explicit user request (e.g. '用 X skill ...')"，由模型根据描述自我约束。这是 superpowers 等成熟 plugin 的现行做法。

## 和 autolearn-sdd-kit 的差异

| 维度 | autolearn-sdd-kit | sdd-kit |
|------|-------------------|---------|
| 阶段数 | 8（brainstorm/research/design/spec/tasks/impl/review/extract-experience） | 5（research/spec/task/impl/review） |
| 命令层 | 14 厚 commands（每个做 orchestration，重复 skill 内容） | 0 commands — 纯 skills-only；plugin runtime 自动把 SKILL.md 的 name 注册为 `/sdd-kit:<name>` |
| 触发方式 | 自然语言 + 命令并存（隐式触发开放） | 显式自然语言"用 X skill …"（description 严格约束）或 `/sdd-kit:<name>` |
| Agent | 9 agents | 0 agents（先做 single-agent, review 建议在 subagent / 新会话里跑） |
| 知识组织 | 4 抽屉（experience / modules / rules / gotchas）+ 3 索引 | 1 wiki + 1 index.md |
| 页面分类 | 按类型前缀硬绑 | 按主题命名 + 类型降级为 frontmatter 属性 |
| 阶段跳转 | 文档互引（tasks.md 顶部写 Spec: xxx） | 文档无强制引用，只允许 `[[wikilink]]` 可选线索 |
| 知识检索 | 向量检索思路（ContextDetective） | Karpathy 显式导航（index → root → 子页）+ R5 新鲜度提示 |
| 语义审计 | review phase 存在但和 impl 边界模糊 | review 独立 skill, 读 spec+diff+wiki, 4 态 (APPROVED/A_W_N/NEEDS_REWORK/SPEC_DRIFT) |
| impl 自验证 | verify 和 execute 混同 | impl 只做 SelfCheck（跑自己的 acceptance）, 语义审计归 review |
