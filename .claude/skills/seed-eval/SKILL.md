---
name: seed-eval
description: "为任意一次插件技能更新，因地制宜设计评估（design）并执行（lab）。design 产出可评审的 Experiment Spec；lab 创建/运行/评估/展示。默认不跑模型，等人确认。"
---
# Seed Eval

两段式：**design**（因地制宜设计评估，产出 Experiment Spec 草案）+ **lab**（创建/运行/评估/展示）。

- 用户说"我要改 X 技能 / 验证 X / 对比 A vs B" → 进 **design**，不要直接 `experiment run`。
- 用户说"跑 / 评估 / 看 Dashboard" → 进 **lab**。

在 `seed-kit-evals` 根目录操作。CLI 是 source of truth：先 `bun run src/cli/index.ts experiment --help` 及子命令 `--help` 确认参数。

---

## design 阶段

目标：产出一份可评审的 Experiment Spec 草案。**人不确认不落盘、不跑模型**。

### 流程

1. **摄入变更**：用户描述 / skill 文件 / diff。先从仓库查证现有资产，不问用户。
2. **策略路由**：按变更类型选 `strategy.type`（见下）。
3. **研究问题 + 任务编排 + arms + presentation**。
4. **用户确认 → 落盘**。

| 变更类型 | `strategy.type` | 主 outcome |
|---|---|---|
| 入口/委托/边界接线 | `sentinel` | 是否按设计走 |
| 新增能力"有没有用" | `value_ab` | 任务结果是否更好 |
| 同能力换策略 | `strategy_ab` | A/B 结果与稳定性 |
| gate/hook 松紧 | `gate` | 该拦拦、该放放 |
| 交互澄清类 | `interaction` | 产物质量 |

### 写作原则

**所有给人看的文字（title、description、arm 名、维度名、band 描述、summary），必须让一个不懂内部代号的人能看懂。**

具体检查：
- **名字说清是什么**：arm 的 title 描述这个 arm 有什么/没什么，不要用产品名或内部代号。场景 title 像短句题名。suite title 是问题本身。
- **描述说清为什么**：scenario 的 description 写「测什么、为什么这样设计、难度在哪」。oss_ref 的 why_selected 写「为什么这个项目适合这个难度」。arm 的 diff_summary 写「和对照的实质差异」。
- **尺子让人看懂**：rubric 每个 target 带 bands，每个分数段写清该段的具体表现——能让作者和评判者对「90 分和 85 分差在哪」达成共识。
- **中文写给人看**：代码标识符、模型名、URL 保留原文；其他一律中文。不在中文里夹英文 artifact 名。
- **不把实现细节当标题**：不要把 `quorum_driver`、`eval_kind`、目录名、文件路径塞进给人看的字段。

详细写作规范见 `docs/scenario-authoring.md` 和 `docs/value-experiment-authoring.md`。design 阶段产出的每个文件都要遵循这两份文档的合同。

### 红线

- design 未确认前不跑模型。
- control 不删光整个插件。
- `minimum_valid_pairs` ≤ trials 数。
- 不把"调用了某 skill"当价值成功的主指标。
- schema:2 Spec 必须有可渲染 presentation。
- 非 sentinel 需 ≥2 arms + control + treatment/candidate 的 reference_arm。

---

## lab 阶段

在 `seed-kit-evals` 根目录操作。

- 创建 → `experiment create <id> --spec-file <path>`
- 运行 → `experiment run <id> --execution-model <profile> --trials 1 --jobs 3`
- 评估 → `experiment evaluate <id> --judge-model <profile> --run-group <id>`
- 浏览 → `./dashboard/start.sh`

"用 X 跑"中的 X 是 execution model。"用 X 评估"中的 X 是 judge model。
