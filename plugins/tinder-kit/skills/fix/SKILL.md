---
name: fix
description: "Disciplined bug-fix flow: build tight red loop, isolate root cause, fix with permanent regression test. Use when fixing bugs, solving test failures, or resolving regressions."
disable-model-invocation: true
---

# Fix — 系统化排障与修复主航道

面向缺陷修复与偶现异常的专门主流程。严格恪守“先造变红命令，再做根治与沉淀防回归测试”的工程纪律。

## 执行流程

### Phase 0: 任务初始化
- 输入：`/fix [slug] "缺陷现象或报错信息"`；
- 自动执行 `forge new <slug> --title "缺陷修复: {slug}"`；
- 更新 `state.json` 的 `phase` 为 `DIAGNOSE`；
- **Completion criterion**：`.forge/tasks/<slug>/` 目录就绪。

### Phase 1: 驱动 `diagnose` 核心回路
- 调起 `diagnose` 技能：
  1. **构建紧凑变红命令**：构造一条能在 2 秒内稳定报错复现的自动化用例/脚本，并在屏幕上展示红色报错；
  2. **最小化复现**：剥离无关变量与请求头；
  3. **假设验证**：向用户展示排序后的 2~3 个根因假设，使用 `[DEBUG-DIAGNOSE]` 插桩验证；
  4. **根治修复**：实施针对性根治，并在接缝处将变红命令固化为**永久性防回归自动化测试**；
  5. **拔桩复原**：彻底清理全部调试插桩；
- **Completion criterion**：针对该 Bug 的自动化回归测试由红变绿（exit 0），且无调试探针残留。

### Phase 2: 全量防回归验证
- 跑通项目全量既有测试套件（若项目有配置），确认既有功能 100% 零回归；若无自动化测试套件，执行关键链路冒烟或自验命令；
- **Completion criterion**：既有测试套件全部 PASS，或关键链路自验证实无回归。

### Phase 3: 沉淀与交接
- 若发现隐蔽的第三方库暗坑或设计缺陷，调用 `domain-modeling` 沉淀一条 Gotcha 进项目根目录 `CONTEXT.md`；
- 调用 `handoff` 生成 `handoffs/01-fix.md`；
- 更新 `state.json` 的 `phase` 为 `COMPLETED`；
- **Completion criterion**：交接文档就绪，状态为 COMPLETED。

### Phase 4: 成果呈递
- 向开发者汇报根因分析、修复策略、新增的防回归测试位置；
- 提示审查 `git diff` 并执行 Commit。
