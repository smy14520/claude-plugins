# seed-kit 验证约定

brainstorm / impl / review 共读（research / wiki 不需要）。gate、review-loop 都在这。

## 原则

- **gate 只卡硬事实**：项目测试命令全过（必须是真实测试框架，true/echo 等伪装被拒绝）+ 质量命令全过。这些是可机械判定的，不依赖语义判断。
- **loop 守好坏**：体验质量、完整性、代码质量走 review-loop 迭代收敛。不做 scoring gate 卡 done。

## PRD 结构

PRD 三段——Goal / Acceptance Criteria / Out of Scope。Slice 内联在 `### [ ] S-NNN` heading 下，验收用 `* [ ]` 条目写：

```markdown
# <Task Title>

## Goal
一段话概述：这是什么、为什么做。

## Acceptance Criteria

### [ ] S-001 用户登录
* [ ] 空提交 → 字段级错误且不发起请求
* [ ] 余额不足 → 402，不写流水
* [ ] 正常登录 → 跳转主页

## Out of Scope
* 不支持社交登录
```

- 一个 `* [ ]` 一个测试用例——正向一条、反向一条、边界一条。
- 技术决策、期望的体验方向自然融入 Goal 和验收条目，不独立成段。

## 三类验证手段（概念分类）

按"谁判定它对"分类验证手段，用于 brainstorm 设计验证和 review-loop 编排：

- **assert** — 机械断言。项目测试框架的测试用例，exit 非零即失败。`seed done` 会执行项目声明的测试命令。
- **judge** — 独立裁判。由独立上下文的 agent 看真实产物（可感知输出/运行实例/生成文件），按 PRD 中描述的方向 + DESIGN.md + rubric 评体验质量。不进 gate，走 review-loop。
- **human** — 真人签收。用于合规/备案/品味等本质不可自动化事项。用 human 覆盖可断言的验收条目是设计气味。

原则：**assert 优先**——能用测试就不要靠 judge，能 judge 就不要靠 human。

## Gate：seed done

`seed done <task> --slice <id>` 只卡硬事实：

1. **项目测试命令**：从项目配置文件自动检测测试命令并执行。必须是真实测试框架（jest/pytest/cargo test 等），true/echo 等伪装命令被拒绝。exit 0 → 通过。
2. **项目质量命令**：自动检测 lint / typecheck / build 等命令并执行。全部 exit 0 → 通过。

全过 → 翻转 slice checkbox。任何一项失败 → 拒绝 done，列出失败原因。

**不做的事**：不验证验收覆盖（那是 review 的职责）、不验证体验质量（那是 judge 的职责）。

## 体验质量：review-loop

正确性靠 gate 的硬事实（测试+质量命令）；体验质量走 **review loop** 迭代收敛。

1. **客观锚**（seed-assert）：重跑项目测试+质量命令 → 不绿则 impl 修，不进语义 review
2. **代码审计**（seed-review）：审代码是否兑现验收条目，查偷懒签名/隐患/工程卫生
3. **产物审计**（seed-judge）：审真实产物是否兑现 PRD 中描述的方向 + DESIGN.md，找 missed-opportunity
4. **证伪**（seed-validator）：对抗性证伪 finding，防误报和过度报告
5. **修复**（seed-impl）：修 survived blocking finding
6. 循环到 `converged`（无 survived blocking）或熔断

收敛靠"无新 blocking finding"，不靠"达到 min 分"。

## Rubric 与 Score-file（review-loop judge 用）

**Rubric**（项目定义，插件不内置）：

```json
{
  "id": "project-quality-v1",
  "scale": {"min": 0, "max": 5},
  "aggregate": {"min_average": 3.5},
  "dimensions": {
    "completeness": {"min": 3, "weight": 1.0},
    "consistency": {"min": 3, "weight": 1.5}
  }
}
```

**Score-file**（独立 judge 生成）：

```json
{
  "rubric_id": "project-quality-v1",
  "scores": {
    "completeness": {"score": 4, "rationale": "核心路径覆盖完整"},
    "consistency": 3
  }
}
```

- rubric/score-file 是 judge 在 loop 里的结构化评分工具，**不是卡 done 的 gate 门槛**
- 维度、门槛、权重由项目定义，插件不解释
- `seed score aggregate` 支持多裁判聚合（median）

## 测试方法：由项目定义，不由插件预置

用什么工具、什么断言手段，由项目在配置文件（package.json/Makefile 等）中声明。插件不预置任何技术栈的测试方法清单——对 Web 成立的测试手段对 CLI / 游戏引擎 / 嵌入式不成立。

方向：读项目配置，用项目声明的命令；项目未声明的不发明。

## 审美：客观骨架 assert，主观品味 judge

- **客观骨架**：配色/字体/布局等有确定值的属性 → 写进测试（assert），`seed done` 执行时自然覆盖
- **主观品味**：层次/精致感/气质 → review-loop judge 审产物，按 PRD 中描述的方向 + DESIGN.md 评

## 硬规则（helper / hook 保证）

- `seed done` 跑项目测试+质量命令，全过才翻 checkbox
- `seed done` 是勾选 checkbox 的唯一合法入口（seed_guard hook 拦截直接编辑）
- 破坏性命令（rm -rf / git reset --hard / git push --force）被 seed_guard 拦截
- 所有 slice done 后，review_on_complete hook 要求 review-loop marker 存在才放行
