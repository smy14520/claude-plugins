---
name: diagnose
description: "针对复杂隐蔽缺陷、竞态条件、偶现异常与性能衰退的严密六步科学排障回路。在遇到疑难 Bug、根因不明的测试硬失败、多模块联动故障、或需要严格变红与插桩证伪时调用（简单语法报错与拼写错误直接就地修复，勿调此技能）。"
---

# Diagnosing Bugs

排障是严密的科学证伪过程。核心铁律：必须先构建出一条能稳定变红的确定性复现命令，再基于执行现场提出可证伪假设并实施根治。

## 阶段操典（Six Phases）

### Phase 1: 构建紧凑变红回路（Build a Feedback Loop）
- 构造一条单一、确定性、尽量快速（<2s）的命令，能够直接复现用户报告的故障并返回非零退出码；
- 手段：特定单元测试用例、curl 脚本、CLI 传参、无头脚本；
- **脱敏原则**：若涉及 Auth Header 或 Secret，统一替换为 `<REDACTED>`；
- **Completion criterion**：在终端显式打印命令调用与红色报错输出。无红命令，排障停止。

### Phase 2: 最小化复现（Minimise）
- 剥离干扰项：去除不相关的请求头、中间件、多余参数与外围依赖；
- 缩短调用链，直到只留下复现故障所必需的最短路径；
- **Completion criterion**：最小化的变红命令依然稳定报错。

### Phase 3: 排序并列出假设（Hypothesise）
- 基于代码库事实，列出 2~3 个具有可证伪性的根因假设；
- 按可能性降序排列，并在屏幕上**向用户完整展示假设清单**；
- **Completion criterion**：假设清单已呈现在对话中。

### Phase 4: 打标插桩（Instrument）
- 针对最高排名的假设进行验证；
- 在关键路径加入带统一前缀 `[DEBUG-DIAGNOSE]` 的临时断言或日志；
- **Completion criterion**：运行复现命令，通过输出的探针日志命中或证伪该假设。

### Phase 5: 修复与沉淀防回归测试（Fix & Regression Test）
- 实施最小且根治的代码修复；
- 将 Phase 1 的变红命令固化为项目代码库中永久生效的自动化测试；
- **Completion criterion**：回归测试由红变绿（exit code 为 0）。

### Phase 6: 拔桩与复测（Clean & Green）
- 全局搜索并清理所有 `[DEBUG-DIAGNOSE]` 探针；
- 重跑项目全量测试套件，确认既有功能零回归；
- **Completion criterion**：全量测试套件 PASS，且无残留调试代码。

## 排障陷阱（Diagnosis Pitfalls）

- **Root-Cause Blindness（表象修复）**：仅在报错位置加判空或捕获异常做防御性涂抹，未消除引发异常的源头状态。
- **Fix-by-Permutation（排列组合盲试）**：缺乏插桩证据时凭直觉连续修改多处逻辑，导致引入新的隐性回归。
