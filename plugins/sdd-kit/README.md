# sdd-kit

**SDD Kit** — Spec-Driven Development + Persistent Wiki Knowledge Layer

新一代 SDD 工具包。基于对 [autolearn-sdd-kit](../autolearn-sdd-kit) 的反思、[Karpathy LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的持久化知识模式、[superpowers](https://github.com/obra/superpowers) 的 skill-first 路线、[claude-code-configs/spf](https://github.com/fantasticcos/claude-code-configs) 的编排经验构建。

## 设计原则

1. **少即是多**：上下文精而少，不追求"完整覆盖"
2. **可控优先**：阶段之间无强制跳转，由用户显式决定
3. **知识复利**：跨需求可复用的资产沉淀到 wiki
4. **不重复代码能说的**：wiki 只写代码查不到的信息

## 四阶段流程

```
research → spec → task → impl
   │        │      │      │
   └────────┴──────┴──────┴──→ 用户主动 ingest → wiki（持久）
```

每阶段独立可用，文档之间**无强制跳转**，但允许 `[[wikilink]]` 作为可选导航线索。

| 阶段 | 职责 | 产物位置 |
|------|------|---------|
| research | 探索、收集资料、发散思考、整理信息 | `.claude/research/<topic>/` |
| spec | 解决决策、明确边界、消除模糊、产出可依赖方案 | `.claude/specs/<name>.md` |
| task | 原子化执行计划（执行者不做决策） | `.claude/tasks/<name>.tasks.md` |
| impl | 按 task 执行代码实现 | 代码本身 |

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

- [x] wiki skill（知识层宪法）
- [ ] research skill
- [ ] spec skill
- [ ] task skill
- [ ] impl skill

## 使用

参见每个 skill 的 SKILL.md。

## 和 autolearn-sdd-kit 的差异

| 维度 | autolearn-sdd-kit | sdd-kit |
|------|-------------------|---------|
| 阶段数 | 8（brainstorm/research/design/spec/tasks/impl/review/extract-experience） | 4（research/spec/task/impl） |
| 命令层 | 14 commands | 0 commands（全 skill，参考 superpowers v5 路线） |
| Agent | 9 agents | 0 agents（先做 single-agent） |
| 知识组织 | 4 抽屉（experience / modules / rules / gotchas）+ 3 索引 | 1 wiki + 1 index.md |
| 页面分类 | 按类型前缀硬绑 | 按主题命名 + 类型降级为 frontmatter 属性 |
| 阶段跳转 | 文档互引（tasks.md 顶部写 Spec: xxx） | 文档无强制引用，只允许 `[[wikilink]]` 可选线索 |
| 知识检索 | 向量检索思路（ContextDetective） | Karpathy 显式导航（index → root → 子页） |
