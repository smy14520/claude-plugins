---
name: diagnose
description: "面向棘手缺陷、偶现异常与性能回退的严密六阶段科学排障回路。在遇到疑难 Bug、根因不明的测试硬失败、多模块联动故障、或需要严格变红与插桩证伪时调用。"
---

# Diagnosing Bugs

面向棘手 Bug 的科学排障纪律。只有在明确说明理由时才跳过阶段。

## Redact（脱敏先行）

在展示 commands、outputs 和捕获的 artifacts 前，**必须先 redact 掉每个 secret**——统一用 `<REDACTED>` 替换。Build loops 要针对环境变量进行，让 credential 留在环境中而不是日志里。捕获的 artifacts 带有 auth headers 时：只引用携带 signal 的必要行。

---

## Phase 1 - Build a feedback loop（构建紧凑变红回路）

**这是排障的核心。** 其他内容都是机械步骤。如果你拥有一个针对该 bug 的 **tight** pass/fail signal，即它会在 _这个_ bug 上稳定变红，你就能找到根因；bisection、hypothesis-testing 和 instrumentation 都只是消费这个 signal。没有变红回路，盯着代码看多久都救不了你。

在这里投入不成比例的精力。**要强硬、要有创造力、拒绝放弃。**

### 构造变红回路的 10 种手段（按序尝试）

1. **Failing test**，放在能触达 bug 的 seam 上：unit、integration、e2e 都可以。
2. **Curl / HTTP script**，打到运行中的 dev server。
3. **CLI invocation**，使用 fixture input，并把 stdout 与 known-good snapshot diff。
4. **Headless browser script**，驱动 UI，并断言 DOM/console/network。
5. **Replay a captured trace**：把真实 network request / payload / event log 保存到磁盘，并在隔离环境中 replay 到代码路径。
6. **Throwaway harness**：启动系统的最小子集（一个 service、mocked deps），用一次 function call 触发 bug code path。
7. **Property / fuzz loop**：如果 bug 是 "sometimes wrong output"，运行 1000 个 random inputs 寻找 failure mode。
8. **Bisection harness**：如果 bug 出现在两个已知状态之间（commit、dataset、version），自动化 "boot at state X, check, repeat"，以便 `git bisect run`。
9. **Differential loop**：用同一 input 跑 old-version vs new-version（或两个 configs），然后 diff outputs。
10. **HITL bash script**：最后手段。如果必须由人点击，用脚本驱动人，让 loop 仍保持结构化，并将捕获的输出反馈给 Agent。

### Tighten the loop（紧凑化回路）

把 loop 当作产品。只要有了 _一个_ loop，就继续 **tighten** 它：
- **更快**：Cache setup、跳过无关 init、缩小 test scope，尽量压到秒级（<2s）；
- **更尖锐**：断言具体 symptom，而不是宽泛的 "didn't crash"；
- **更确定**：Pin time、seed RNG、isolate filesystem、freeze network。

### Non-deterministic bugs（非确定性 / 偶现 Bug 放大）

目标不是 clean repro，而是 **higher reproduction rate（更高复现率）**。循环触发 100x、parallelise、加压、缩小 timing windows、注入 sleeps。50% 复现率的 bug 可以调试；1% 不行。持续提高复现率，直到它可稳定调试。

### When you genuinely cannot build a loop（无法构造回路时的出口）

停下来并明确说明。列出尝试过什么。向用户请求：(a) 能复现的环境访问权限，(b) 经脱敏的 captured artifact（HAR、log dump、core dump、录屏），或 (c) 添加临时生产 instrumentation 的许可。**严禁** 在没有变红回路时直接空想假设。

### Completion criterion
- [ ] **Red-capable**：能在该 bug 上变红、修复后变绿；
- [ ] **Deterministic**：每次运行结论稳定（偶现 bug 已放大至高复现率）；
- [ ] **Fast**：秒级反馈；
- [ ] 在终端显式展示该 command 及已脱敏的红色报错输出。无红命令，排障停止。

---

## Phase 2 - Reproduce + minimise（复现与最小化）

运行 loop，亲眼看到 bug 出现。

确认：
- [ ] Failure mode 确实是用户报告的那个，而不是附近的偶发无关失败；
- [ ] 捕获了 exact symptom（error message、wrong output、slow timing），用于后续验证 fix。

### Minimise（削减干扰）
一旦变红，把 repro 缩到 **仍会变红的最小场景**。逐个削减 inputs、callers、config、data 和 steps；只保留 failure 的 load-bearing（承重）部分。
- **Completion criterion**：每个剩余元素都是 load-bearing，移除任意一个都会让 loop 变绿。

---

## Phase 3 - Hypothesise（排序可证伪假设）

在测试任何假设前，生成 **3~5 个 ranked hypotheses**。单假设会锚定在第一个看似合理的直觉上。

每个 hypothesis 必须是 **falsifiable（可证伪）**：说明它会做出什么具体预测。
> **格式**：`"If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."`

如果无法给出明确预测，这就是无依据的 vibe；丢弃或打磨它。
**测试前把排序后的假设清单完整展示给用户**。用户常常拥有领域知识可立即纠偏或排除已知项。

---

## Phase 4 - Instrument（靶向打标插桩）

每个 probe 都必须映射到 Phase 3 的某个具体预测。**一次只改变一个变量。**

### 工具优先级（Tool Preference）
1. **Debugger / REPL inspection**：一个断点胜过十条 logs；
2. **Targeted logs**：放在能区分不同 hypotheses 的 boundaries 上；
3. **严禁 "log everything and grep"**。

给每条调试日志加统一前缀，例如 `[DEBUG-DIAGNOSE]`，以便最后一次性清理。

### Perf branch（性能衰退分支）
对 performance regressions，加日志通常是错的（会改变性能特征）。改为**先建立基线测量（timing harness、profiler、query plan），然后 bisect。先 measure，再 fix。**

---

## Phase 5 - Fix + regression test（根治与防回归测试）

在 fix 前写 regression test，但前提是存在 **correct seam（正确接缝）**。

- **Correct seam** 是测试能以真实调用链路触发 real bug pattern 的地方。如果可用 seam 太 shallow（bug 需要多个 callers，但测试只有 single-caller），那里的测试只会给出虚假信心；
- **如果不存在 correct seam**：这本身就是架构发现！记录下来，说明系统设计缺乏防守接缝。

实施步骤：
1. 将 minimised repro 转化为该 seam 上的 failing test；
2. 亲眼看它 fail；
3. 实施针对性根治代码；
4. 亲眼看它 pass；
5. 重新针对原始（未最小化）场景运行 Phase 1 feedback loop，确认彻底修复。

---

## Phase 6 - Cleanup & Knowledge（拔桩与沉淀）

完成退出清单：
- [ ] 原始场景不再复现（重跑 Phase 1 loop 确认变绿）；
- [ ] 防回归测试稳定通过；
- [ ] 全局 grep `[DEBUG-DIAGNOSE]`，彻底清理所有临时插桩；
- [ ] 临时丢弃型 harness/探针已清理；
- [ ] **把证实的假设写入 commit message**，让下一个排障者能够溯源学习。

---

## 经典排障陷阱（Anti-Patterns）

- **Root-Cause Blindness（表象涂抹）**：仅在报错位置加判空或空 try-catch 掩耳盗铃，未消除引发异常的源头状态。
- **Fix-by-Permutation（排列组合盲试）**：缺乏插桩证据时凭直觉连续修改多处逻辑，导致引入新的隐性回归。
- **No-Loop Hypothesising（空中楼阁）**：在没有可运行的变红命令前，直接阅读代码长篇大论假设根因。
