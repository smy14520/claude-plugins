# sdd-next

> 新一代轻量 SDD Claude Code 插件草案。目标是在 `sdd-kit` 旁边重建一个更清晰、更少状态、更显式触发的工作流。

`sdd-next` 不是旧 `sdd-kit` 的继续打补丁版，而是一次重新收敛：保留 PRD-first、行为级 slices、evidence、semantic review、显式 wiki 的精华，去掉历史遗留、过度状态机、过多底层命令、阶段自动串联和执行层噪音。

## 核心原则

```text
用户掌握阶段切换
PRD 掌握需求边界
代码体现真实进度
evidence 约束完成质量
wiki 承载长期项目经验
helper 只做机械动作
```

## 五个显式阶段

```text
research   外部资料收集与资料包整理
brainstorm 需求访谈、边界决策、PRD 收敛
impl       按 PRD 执行代码，少状态、可断点续作
review     用户主动触发的 PRD + diff + evidence 审计
wiki       用户主动触发的长期项目知识沉淀与查询
```

阶段之间不自动跳转：

- `research` 不自动进入 `brainstorm`。
- `brainstorm` 不默认检索所有 research / wiki，只读取用户明确指定的资料。
- `impl` 不自动 publish wiki。
- `review` 不自动修代码。
- `wiki` 不自动摄入每次实现结果。

## 新数据层建议

```text
.sdd/
├── research/
│   └── <topic>/
│       ├── index.md
│       ├── summary.md
│       ├── sources/
│       └── notes/
└── packages/
    └── <package>/
        ├── prd.md
        ├── progress.md
        ├── evidence.md
        └── review.md

.wiki/
└── <project knowledge pages>
```

`.sdd/` 承载当前需求工作流；`.wiki/` 承载长期项目知识；代码仍是实现事实源。

## 为什么新开目录

旧 `sdd-kit` 多轮迭代后已经混入不少历史层：旧 `.claude` 知识管理模型、`.arbor` 状态机、旧 autolearn 命令、过期 README、过多 helper 子命令，以及一些曾经存在后来删除的设计痕迹。

新目录的目标是从用户真实使用体验重新出发：

- 少即是多。
- 代码即进度。
- PRD 是边界，不是仪式。
- wiki 必须主动触发，不能自动污染。
- research 是资料包，不是方案决策器。
- impl 可以用 workflow / agent team 加速，但核心状态不能复杂。

详细设计见 [`DESIGN.md`](./DESIGN.md)。