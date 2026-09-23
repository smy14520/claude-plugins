---
name: fix
description: "系统化缺陷修复主流程：构建确定性变红回路、定位根因、编写永久性防回归测试。在用户报告明确 Bug 或需要排查修复故障时使用。"
disable-model-invocation: true
---

# Fix — 系统化排障与修复主航道

面向缺陷修复与 Heisenbug / 复杂故障的专门主流程。严格恪守“先造变红命令，再做根治与沉淀防回归测试”的工程纪律。

## 执行流程

### Phase 0: 任务初始化
- 输入：`/fix [slug] "缺陷现象或报错信息"`；
- 自动执行 `forge new <slug> --title "缺陷修复: {slug}"`；
- 更新 `state.json` 的 `phase` 为 `DIAGNOSE`；
- **Completion criterion**：`.forge/tasks/<slug>/` 目录就绪。

### Phase 1: 驱动 `diagnose` 核心回路
- 执行：**Call the Skill tool for "diagnose"**：
  1. **构建紧凑变红命令**：构造一条能在 2 秒内稳定报错复现的自动化用例/脚本，并在屏幕上展示红色报错；
  2. **最小化复现**：剥离无关变量与请求头；
  3. **假设验证**：向用户展示排序后的 2~3 个根因假设，使用 `[DEBUG-DIAGNOSE]` 插桩验证；
  4. **根治修复**：实施针对性根治，并在接缝处将变红命令固化为**永久性防回归自动化测试**；
  5. **拔桩复原**：清理所有 [DEBUG-DIAGNOSE] 插桩；
- **Completion criterion**：针对该 Bug 的自动化回归测试由红变绿（exit 0），且无调试插桩残留。

### Phase 2: 全量防回归验证
- 跑通项目全量既有测试套件（若项目有配置），确认既有功能 100% 零回归；若无自动化测试套件，执行关键链路冒烟或自验命令；
- **Completion criterion**：既有测试套件全部 PASS，或关键链路自验证实无回归。

### Phase 3: 沉淀与交接
- 若发现隐蔽的第三方库陷阱，使用 `Write` 工具在 `.forge/wiki/gotcha/` 沉淀一条 Gotcha 或提议写入项目规则库；
- 将修复总结与防回归验证交接文档写入 `.forge/tasks/<slug>/handoffs/`；
- 更新 `state.json` 的 `phase` 为 `COMPLETED`；
- **Completion criterion**：交接文档就绪，状态为 COMPLETED。

### Phase 4: 成果呈递
- 向开发者汇报根因分析、修复策略、新增的防回归测试位置；
- 提示审查 `git diff` 并执行 Commit。
