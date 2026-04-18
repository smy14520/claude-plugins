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
   │        │      │      │        │
   │        │      │      │        └─ 独立审计（读 spec + diff + wiki）
   │        │      │      └─ 自运行 acceptance（机械自检，不做语义审计）
   └────────┴──────┴──────┴────────┴──→ 用户主动 ingest → wiki（持久）
```

每阶段独立可用，文档之间**无强制跳转**，但允许 `[[wikilink]]` 作为可选导航线索。

| 阶段 | 职责 | 产物位置 |
|------|------|---------|
| research | 探索、收集资料、发散思考、整理信息 | `.claude/research/<topic>/` |
| spec | 解决决策、明确边界、消除模糊、产出可依赖方案 | `.claude/specs/<name>.md` |
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
- [x] research skill（探索 + raw/refined 分层 + 显式 ingest 提议）
- [x] spec skill（决策门户 + 内容契约 + 无决策史）
- [x] task skill（原子拆解 + DAG + strict-atomic/lean 双模式 + 无 wikilink）
- [x] impl skill（四态状态机 + 可验证 acceptance + 不静默决策 + 末尾 wiki-ingest 建议）
- [x] review skill（独立语义审计 + 4 态 + 读 spec/diff/wiki + 不改代码）

## 使用

**只接受显式 slash 命令触发。所有 skill 都设置了 `disable-model-invocation: true`，不会被 Claude 自作主张激活。**

```bash
# 五阶段主流程
/sdd-kit:research <topic>            # 探索主题，产出 .claude/research/<topic>/
/sdd-kit:spec <name>                 # 写 spec，产出 .claude/specs/<name>.md
/sdd-kit:task <spec-name-or-path>    # 拆 task，产出 .claude/tasks/<name>.tasks.md
/sdd-kit:impl <task-id-or-file>      # 执行 task，SelfCheck 后报 4 态 (DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED)
/sdd-kit:review <task-id-or-file>    # 独立语义审计，报 4 态 (APPROVED/APPROVED_WITH_NOTES/NEEDS_REWORK/SPEC_DRIFT)

# 知识沉淀层（独立于 SDD 流）
/sdd-kit:wiki <intent and content>   # ingest / query / lint 三选一，由内容自动派发
```

**推荐**: `/sdd-kit:review` 最好在**新会话 / subagent** 里跑，避免写代码的同一上下文自我审查（自查偏差）。

阶段之间**不自动跳转**。wiki 也必须显式触发。

> **为什么要显式触发？** 避免 skill "过度触发"（Superpowers 曾因 1% 阈值被 Reddit 诟病烧 token）。中文用户还多一层好处：slash 命令是英文字符精确匹配，不依赖模型对中文意图的理解。

## 和 autolearn-sdd-kit 的差异

| 维度 | autolearn-sdd-kit | sdd-kit |
|------|-------------------|---------|
| 阶段数 | 8（brainstorm/research/design/spec/tasks/impl/review/extract-experience） | 5（research/spec/task/impl/review） |
| 命令层 | 14 厚 commands（每个做 orchestration，重复 skill 内容） | 6 薄 commands（仅作为 skill 入口，单一真相源仍在 skill） |
| 触发方式 | 自然语言 + 命令并存（隐式触发开放） | 仅显式 `/sdd-kit:xxx`（`disable-model-invocation: true`） |
| Agent | 9 agents | 0 agents（先做 single-agent, review 建议在 subagent / 新会话里跑） |
| 知识组织 | 4 抽屉（experience / modules / rules / gotchas）+ 3 索引 | 1 wiki + 1 index.md |
| 页面分类 | 按类型前缀硬绑 | 按主题命名 + 类型降级为 frontmatter 属性 |
| 阶段跳转 | 文档互引（tasks.md 顶部写 Spec: xxx） | 文档无强制引用，只允许 `[[wikilink]]` 可选线索 |
| 知识检索 | 向量检索思路（ContextDetective） | Karpathy 显式导航（index → root → 子页）+ R5 新鲜度提示 |
| 语义审计 | review phase 存在但和 impl 边界模糊 | review 独立 skill, 读 spec+diff+wiki, 4 态 (APPROVED/A_W_N/NEEDS_REWORK/SPEC_DRIFT) |
| impl 自验证 | verify 和 execute 混同 | impl 只做 SelfCheck（跑自己的 acceptance）, 语义审计归 review |
