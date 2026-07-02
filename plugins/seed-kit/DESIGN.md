# seed-kit 设计文档

seed-kit 是上一代工作流的轻量继任者：取其精华（PRD source of truth、真实验证、wiki 导航层），去其糟粕（多层状态机、24 个命令、为已删除特性残留的 schema）。

## 动机

外部调研（spec-kit / Kiro / Trellis / Ralph loop / OpenSpec / Anthropic harness 研究）收敛出的不变量：

> **PRD 是需求的 source of truth，文件系统是状态的 source of truth，git 是进度的 source of truth，硬事实是正确性的 source of truth。**
> 在这四个锚点之上，流程越轻、命令越少、阶段越不强制，存活率越高。

第四条只敢说"正确性"，不敢说"质量"——这是刻意的。质量分两半，本性相反，要用相反的工具：

- **可验证的一半**（余额算对、422、契约、转账不计收支）：能写测试，二值 gate（exit 0）正合适。
- **不可验证的一半**（好不好用、顺不顺手、好不好看、优不优雅）：写不出能由命令直接断言的测试。二值 gate 用在这里不是"不够"，而是**有害**：它在通过线以上没有提升动力，把一条本无天花板的质量轴**封顶在最小可过**；而"按 spec 通过"又把模型从生成模式切到合规模式。二者叠加，产出一个能过测试却没法真实使用的"半成品"。

所以这一半不能交给 exit code 或插件内置审美，只能靠**测试保持绿不回归 + 一个感知真实产物、按 PRD 中描述的方向打分的独立 judge 在环**。承认它、把它做顺，比假装 exit code 能替代它更稳。

**Gate 边界**：gate 只卡硬事实——测试全过 + 质量命令全绿 + 产物存在。体验质量不进 gate，走 review-loop 迭代。

被反复证明失败的设计恰好是上一代工作流的病灶：过重状态机（"reinvented waterfall"）、过多命令的 context tax、依赖模型自觉的口头约束、大体量生成文档、逐条 obligation 合规框架。

## 设计原则

1. **五个 skill 全部由用户主动触发，互不自动耦合。**
2. **纯 Markdown 状态，没有状态机。** `prd.md` 的 slice checkbox + git log 就是全部进度；断点续作 = 读 prd.md + git log。没有 task.json。
3. **helper 只做确定性的状态读写。** 脚手架、解析校验、执行测试/质量命令、勾选 checkbox——全是确定性动作，不调用 LLM。`seed done` 是唯一的硬 gate。
4. **命令面极小：核心 3 个（new / status / done）+ score + wiki 家族。**
5. **hook 只守底线：** 拦截破坏性命令；拦截绕过 gate 手工勾选 checkbox。
6. **用户拥有 commit。**

## 五个 skill

### research — 给需求收集外部资料
### brainstorm — 需求收敛访谈

职责：把模糊想法收敛成可执行的 PRD。终点：`seed new <task>` + 写入 `prd.md`（Goal + Acceptance Criteria + Out of Scope，slice 内联在 `### S-NNN` heading 下，验收用 `* [ ]` 条目写）。

- PRD 中描述的方向是期望而非检查清单——给 agent 创作方向，给 judge 评审依据。

### impl — 执行 PRD

职责：按 `## Slices` 顺序执行，一个 agent 依次做所有 slice（保持品质连贯）。`seed done` 跑测试+质量命令+验产物 → 翻 checkbox。

### review — 语义审计
### wiki — 项目知识层

## Artifact 结构

```
.arbor/
├── tasks/<task>/
│   ├── prd.md        # 唯一状态：slice 内联（### [ ] S-NNN heading + prose）
│   ├── review.md     # review 追加记录
│   ├── done-logs/    # seed done 日志
│   └── notes/        # impl 过程备注（可选）
└── research/<topic>/
```

### PRD 骨架（slice 内联）

```markdown
# <标题>                            # prd.md

## Goal
## Acceptance Criteria
### [ ] S-001 <标题>
## Out of Scope
```

```markdown
### [ ] S-001 <标题>

* [ ] <可测试的行为路径>
* [ ] <可测试的行为路径>
```

## helper 命令面（核心 3 个 + score + wiki）

| 命令 | 做什么 |
|---|---|
| `seed new <task>` | 脚手架 `.arbor/tasks/<task>/` |
| `seed status [<task>]` | slice 进度、验收条目列表、下一个未完成 slice、结构校验 |
| `seed done <task> --slice S-NNN` | 跑项目测试+质量命令+验产物，全过则翻 checkbox |
| `seed review-mark <task> --verdict <reason>` | 落 review-loop 终态 marker |
| `seed score aggregate` | 多裁判评分聚合（review-loop judge 用） |
| `seed wiki ...` | wiki 家族 |

## 防 AI 偷懒方案（分层）

1. **写需求时就写可证伪的验收条目**（brainstorm 层）：每条一个可测试的行为路径（正向/反向/边界）。PRD 中描述的方向给 agent 创作空间，不进 gate。
2. **硬 gate，只卡硬事实**（helper 层）：`seed done` 跑项目测试命令（exit 0 + >0 tests）+ 质量命令（lint/typecheck/build 全 exit 0）+ 验产物存在。不过则拒绝。
3. **hook 守底线**（hook 层）：拦截直接改 checkbox、破坏性命令。
4. **生成者 ≠ 验证者**（review 层）：review 用干净上下文逐验收条目对账，查偷懒签名；judge 看真实产物按 PRD 中描述的方向评体验。
5. **一个 agent 做所有 slice**（流程层）：保持跨切片品质连贯，不做 per-slice sub-agent dispatch。

第 2、3 层是机械的（脚本保证），第 1、4、5 层是流程约定。

### 两种失败模式

**蒙混**——弱化断言、假测试、吞异常——靠第 2、3 层机械堵死。

**诚实地最小满足**——agent 精确做了"刚好过 gate"的最小实现。这不是 bug，是把不可验证质量塞进二值 gate 的设计产物。解法：
- **测试通过不代表品质到顶。** `seed done` 代表硬事实通过，不代表品质没有上限。
- **PRD 中描述的方向是期望。** 不进 gate——传递"这是你想做成的样子"而非"这是你必须证明的条目"。
- **judge 在环看真实产物。** 评判不由 helper 机械化；helper 只校验 artifact 存在与 score 形状。

## 三类验证手段（概念分类）

- **assert** — 机械断言。项目测试框架，exit 非零即失败。`seed done` 执行。
- **judge** — 独立裁判。看真实产物，按 PRD 中描述的方向 + rubric 评。走 review-loop，不进 gate。
- **human** — 真人签收。用于本质不可自动化事项。

原则：assert 优先，能 judge 不叠加 human。

## 从上一代工作流的取舍清单

**带走**：PRD 的 Goal + Acceptance Criteria + Out of Scope 三段结构；brainstorm 访谈循环；research index-first 工作区；wiki 四命令；破坏性命令拦截。

**丢弃**：六态 lifecycle、task.json、obligation 框架、evidence 目录、run-check、烟雾命令检测、AC 覆盖校验、amendment 编号仪式。

## 实施路线

- **M1 骨架**：`tools/seed.py`（new / status / done）+ 单测 + 模板
- **M2 skills**：brainstorm / impl 两个 SKILL.md + guard hook
- **M3 外环**：research / review / wiki + review-loop
- **M4 实战校验**：拿真实需求跑全链路，按失败模式补约束
