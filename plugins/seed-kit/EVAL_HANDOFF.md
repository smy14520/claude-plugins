# seed-kit 评估与栈无关化改进 — 工作交接

> 给接手者（人或 AI）：我们在做什么、怎么做、想什么、走到哪。读完应能接手跑评估、改 seed-kit，且不重蹈覆辙。
> 最后更新：2026-06-28

---

## 1. 我们在做什么

评估并改进 **seed-kit**——一个 Claude Code 插件（栈无关的 PRD-first 开发工作流），用真实终端跑 benchmark 对比 **seed-kit / baseline（裸）/ trellis（CLI 工作流）**，目标是让 seed-kit 既能守住核心哲学（**机制在插件，标准在项目**），又能产出高质量成品。

- seed-kit：`/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit/`
- 评估 harness：`/Users/camellia/Personal/Code/claude/claude-plugin-auto-evolution/`
- 项目规则（**必读，所有判断的依据**）：`/Users/camellia/Personal/Code/claude/claude-plugins/.claude/rules/`（`workflow-design.md`、`prompt-design.md`）

---

## 2. 核心设施：怎么用真实终端跑 benchmark

**不是模拟**。`drive.mjs` 用 claudemux spawn **真实的 Claude Code session**（provider=`ali-qwen`，称 cca），CCA 真实跑命令、真实用工具。

**三路 harness**：
- `seed-kit`：`--plugin-dir plugins/seed-kit` 加载插件，按 skill 跑
- `baseline`：裸 Claude Code，无工作流约束
- `trellis`：装 trellis CLI（`trellis init --claude` 注册 agents/skills/hooks）

**benchmark**：`eval/benchmarks/<name>/spec.md`（需求 + AC + `## test-command`）+ 可选 `DESIGN.md`（审美标准）+ `traps.md`（评估员判分依据，harness 看不见）
- `react-todo`：Vite+React+Vitest+playwright，**有审美 judge 维度**（S-005 拆 assert: scrollWidth/line-through/窄屏 + judge: 主观精致）
- `csv-toolkit`：纯 node，**assert-only**（无 judge）

**跑法**：
```bash
cd /Users/camellia/Personal/Code/claude/claude-plugin-auto-evolution
node src/drive.mjs <benchmark> <harness> <provider>
# 例: node src/drive.mjs react-todo seed-kit ali-qwen
```

**drive 是多轮自动驱动**（全程无人提问）：
1. spawn session（cwd=runDir）→ sanity（pwd + 验 seed 可用）
2. **brainstorm 循环**：发 `brainstorm(bm)` prompt → CCA 写 PRD（`.arbor/tasks/<task>/prd.md` + `slices/S-NNN.md`）→ `readState` 看到 slice 就 break
3. **impl 循环**（最多 15 turn）：turn 0 发 `impl(bm)`，之后每轮 `readState` → `nudge`（基于状态发下一句）→ 直到 `done` 或 `escalated`
4. 产出 `runs/<bm>-<h>-<stamp>/`：`summary.json`（结果）、`drive.log`（每轮状态）、`dialogue.md`（精简）、`trace.md`（完整工具流，审 review-loop 真假看这）、`.arbor/tasks/<task>/`（prd/slices/evidence）、源码

**关键**：CCA 真实执行——跑 `seed run-check`/`npm test`/`npm run build`/playwright 截图、用 Workflow 工具启动 review-loop（async 多 agent）、TaskOutput 取结果、`seed review-mark` 落 marker。Stop hook（`hooks/review_on_complete.py`）在所有 slice done 时强制 task 级 review-loop marker。

---

## 3. seed-kit 的机制

- **5 skill**：research / brainstorm / impl / review / wiki
- **AC 驱动**：每个 slice 的 `## 验收`（`AC-N`，可证伪 Given/When/Then 含失败路径）+ `## 验证`（`[kind] <obligation-id> (AC-N): <可观测行为>`）
- **三类 kind**：`assert`（机械断言，exit 0 才过）/ `judge`（独立裁判主观产物）/ `human`（真人签收）
- **gate 守对错，loop 守好坏**：`seed done` = assert 全绿 + AC 覆盖校验（每 AC 有 obligation 绑它）；体验质量走 review-loop 迭代收敛，不做 scoring gate 卡 done
- **review-loop**（`templates/review-loop.template.js`）：async Workflow 多 agent——`seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（批量证伪 finding）/ `seed-assert`（客观锚）/ `seed-impl`（修 blocking），loop 到 `converged`（无 survived blocking）或熔断
- **seed CLI**（`tools/seed.py`）：`new/status/run-check/done/review-mark/score`，机械 gate + AC 覆盖校验 + 烟雾命令硬阻断（裸 curl/echo 拒绝落盘）

---

## 4. 已修复的问题（都在 harness 层，非插件本体）

- **`benchmark.mjs` slice 解析**：regex 要求 `(surface)` 后缀，AC 重构删了 surface → 解析空 → prompt 没列 slice → CCA 砍 scope（csv 只做 2/5 slice）。已修（surface 可选）。
- **`harness/seed-kit.mjs` 是重构前旧版**：sanity 的 `readlink seed` 把插件路径灌给 CCA → CCA 把 prd 写到 `plugins/seed-kit/.arbor/`（双重 .arbor）；impl prompt 还指示每 slice review-loop；readState 读旧 marker 路径。已同步（整体一次 review-loop + task 级 marker + sanity 改 `pwd` 锚定 cwd）。

---

## 5. 当前核心主题：栈无关哲学（最重要的思考）

### seed-kit 最高哲学：机制在插件，标准在项目
插件提供机制（AC 驱动、gate、loop、helper），项目定义标准（UI 规范、质量门槛、参考产品）。换项目不改插件。

### trellis 为什么综合质量更好？——不是 comprehensive
逐步想清楚：最初猜"测试数 118 vs 41"，被推翻（代理指标）；猜"AC 绑定测试天花板"，部分对；真实审计后发现——**trellis 的优势是栈无关写法**：
- agent 写 `Run the project's lint and typecheck commands`，**不硬编码工具名**（grep playwright/react 零匹配）
- **标准外置到项目**（`.oxlintrc.json` 项目配、`.trellis/spec/` 项目填）
- **可迁移性自检**：判据是"agent 原样拷到 Python 后端/Rust CLI/RN 项目，能否不改一字工作"

CCA 写什么测试，取决于"审查者查什么"——trellis-check 查代码质量（跑 lint/build）并 self-fix，seed-kit review-loop 只查 AC 兑现 + 审美。**审查维度决定产物质量面**，不是测试数量。

### seed-kit 的违规——`verification.md` 是震中
workflow 全面排查（7 agent 读全部 prompt）：**seed-kit 的 helper 代码（seed.py）已经栈无关，问题全在文档层**。震中是 `verification.md`（brainstorm/impl/review 共读），却塞了 Web 标准：第 70-78 行枚举 Playwright/computed-style/a11y/Pact/Unity/Unreal/snapshot/schema 当"测试方法参考词汇"——**这是 AC 重构时"帮 brainstorm 写专业 obligation"善意越界加的**，正是被哲学没挡住的违规。

---

## 6. 修改清单（待执行，按杠杆）

**第一梯队（消源头 + 防再犯）**：
1. `verification.md` 第 70-78 行『测试方法参考词汇』整节**删除** → 改一句机制指引（手段由项目定义，读项目 DESIGN.md/rules）
2. `CLAUDE.md`（根 + seed-kit）补**判定式哲学**：*"一行能否留在插件，取决于是否对所有技术栈同等成立；对 Web 成立但对纯 CLI/游戏引擎/嵌入式不成立的，是项目标准，移到项目"* + 正反白名单

**第二梯队**：`seed-judge.md`（产物形态"截图/URL"→抽象）/ `verification.md` 审美骨架（留判定式删 Web 举例）/ 去 Playwright、curl-sf / review-loop judge prompt 去"前端页面"

**第三梯队**：DESIGN.md（@ts-ignore→抑制性注解）、prd.md（质量基线 UI/CLI/配色→"可感面形态不限"）、AC 示例去前端表单

**独立判断（不盲信 workflow）**：`review-loop.template.js` category enum（correctness/lazy-signature/hazard/missing-deliverable/experience）**保留**——5 类都栈无关，是机制不是标准。

**验收判据**：每处改完，文件原样拷到 Rust CLI / C++ 引擎 / Go 后端项目，能否不产生栈噪音工作。

---

## 7. 反模式教训（必读，别重蹈）

1. **不要把一次性问题当永久规则（面多加水）**：如"visual 测试没配 vitest exclude"是 CCA 这次的配置疏忽，不该塞进 seed-review 当永久审查项。原则见 `workflow-design.md`「不为一次失败加长期负担」。
2. **不要把标准塞进插件**：a11y AA 4.5 / 废弃 API（onKeyPress）/ 不可变性 / 对比度是**项目标准**。"非封闭""举例而已""留余地"这些修饰语是标准泄漏的伪装，**挡不住锚定效应**——Rust CLI 读到 Playwright 清单仍觉得 seed-kit 关心 Web。
3. **不要用代理指标**：测试数、CSS 字数 ≠ 质量。真实审计推翻了"trellis 118 > seed-kit 41"的简单排名——要测**真实覆盖面 + 真实渲染 + 真实 bug**。
4. **不要猜测，要核实代码**：多次因没核实下错结论（"-t 精确绑是根因"猜错了；"伪造 marker"猜错了）。每次都该读代码/trace 实锤。
5. **改进要机制层补强，不是换一批标准枚举**：把"前端/API/游戏/CLI"换成"Web/Mobile/Desktop"仍是泄漏。正确形态是"跑项目工具"，不是"插件预置清单"。

---

## 8. 真实质量审计的发现（四路对比，都 ali-qwen）

| | seed-kit这次 | seed-kit之前 | baseline | trellis |
|---|---|---|---|---|
| 测试 | 41 | 67 | 66 | 118 |
| 真实质量 | 合格偏上 | 良好 | 合格 | 良好 |

- **四个项目都有同一个 reload id 冲突 bug**（`let nextId=1` + loadTodos 不基于 max id 重置）——spec 没要求的隐性维度，所有方法盲区
- seed-kit 这次 `npm test` 实际失败（加了 visual 测试没配 vitest exclude）——之前数"41 passed"完全漏了
- review-loop 的盲区：**工程实践（lint/build 入口）、a11y、隐性状态一致性**——这些 trellis-check 靠跑 oxlint 拦了一部分
- trellis 审美 blind（traps.md 确认），seed-kit 审美强（唯一空状态 + seed-judge 真审 DESIGN.md）——**两者盲区互补**

---

## 9. 待办 / 悬而未决

- **第一梯队修改**（verification.md 删节 + CLAUDE.md 判定式）——等执行
- **`missing-deliverable=blocking` 改动**（review-loop.template.js 第 159 行）：之前因"S-004 持久化零测试"加的，**可能是同类"症状当规则"问题**，待审视是否撤
- 改完**重跑 react-todo seed-kit 验证**（看栈无关化 + 判定式后，质量与流程）

---

## 10. 协作约定

- 默认中文，代码/命令/路径/JSON 保持原样
- **少即是多**：规则写成方向不是补丁清单；给模型留判断空间
- 改 seed-kit 前必读 `.claude/rules/`（workflow-design.md + prompt-design.md）——那里是判断"该不该改、怎么改"的依据
- **agent 不自动 commit**；改动落 evidence/状态，不替用户决定
