---
name: diagnose
description: "Disciplined diagnosis loop for bugs, test failures, and regressions. Use when something is broken, throwing, failing, slow, flaky, or when asked to 'diagnose' or 'debug'."
---

# Diagnosing Bugs

排障是严密的科学证伪过程。核心铁律：没有构建出能稳定变红的最小反馈命令之前，绝不提出任何修复假设或修改生产代码。

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

## 反模式（Anti-Patterns）

- **Theorising Without a Repro**：在没有变红命令前读代码脑补理论、凭感觉猜 Bug。
- **Fix-by-Permutation**：乱改代码碰运气，寄希望于“这样改改说不定就好了”。
- **Leaving Artifacts**：修复完成后忘记清理调试日志或临时脚本。
- **Fixing Without Regression Test**：仅手动验证通过，未沉淀自动化用例，导致未来重复踩坑。
