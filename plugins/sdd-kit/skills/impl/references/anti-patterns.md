# Impl 反模式

已观察到的失败模式，其中许多继承自先前的 SDD 工具链。全部应避免。

---

## 1. 未运行验收即声称 DONE

**症状**：状态行显示 DONE；检查发现 `pnpm test` 从未运行，或运行后失败，或运行了错误的路径。

**错误原因**：违反了核心的"不做未验证声明"规则。传播虚假通过信号。

**修复方式**：SelfCheck 步骤必须执行每一条 `acceptance:` 条目。如果命令无法运行（环境问题），状态应为 BLOCKED，而非 DONE。

---

## 2. 静默做设计决策以解除阻塞

**症状**：任务对重试次数存在歧义。执行者静默选择了"3 次尝试"并标记 DONE。

**错误原因**：该选择现在不可见了；未来读者会假设"3"是 spec 的意图。下游决策会在隐藏的猜测之上叠加。

**修复方式**：遇到歧义即停止 → 发出 NEEDS_CONTEXT 并附上具体问题。让用户（或 spec）决定。如果紧急情况下必须猜测，标记 DONE_WITH_CONCERNS 并明确注明"在 spec 未指导的情况下选择了 3 次尝试"。

---

## 3. 将 BLOCKED 伪装为 DONE_WITH_CONCERNS

**症状**：依赖不可用，执行者写了并不真正满足 acceptance 的"存根"代码，标记为 DWC。

**错误原因**：DWC 意味着 acceptance 通过但有顾虑。如果 acceptance 未通过，那是 BLOCKED（或 NEEDS_CONTEXT）。

**修复方式**：DWC 要求 acceptance 实际通过。伪造 acceptance 的存根是在撒谎。

---

## 4. 修改验收标准使其通过

**症状**：任务要求"pnpm test tests/xhs.test.ts passes"。测试失败。执行者修改了测试（或任务的 acceptance）使其通过，然后声称 DONE。

**错误原因**：acceptance 是权威的。修改它等于破坏契约。

**修复方式**：

- 如果测试本身有误 → 这是任务层面的问题，退回 NEEDS_CONTEXT
- 如果实现有误 → 修复 impl，重新 SelfCheck
- 绝不要从 impl 编辑任务的 `acceptance:` 字段

---

## 5. 在任务提交中夹带清理工作

**症状**：任务 T-003 的范围是添加一个 handler。执行者还"顺便"重构了一个无关文件。

**错误原因**：范围蔓延，审查影响半径扩大，依赖纠缠，回滚复杂度增加。

**修复方式**：保持任务聚焦于其交付物。相邻的清理工作应作为后续任务。

---

## 6. "运行了测试"但不看输出

**症状**：状态显示 DONE，但 `pnpm test` 输出中实际有 2 个失败（执行者只扫了来自另一个测试套件的最终"passed"行）。

**错误原因**：敷衍的 SelfCheck。

**修复方式**：SelfCheck 意味着解析退出码 + 检查输出中实际的失败数量。如有疑问，将输出行转储给用户。

---

## 7. 自动推进到下一个任务

**症状**：T-003 报告 DONE 后，impl 未经用户输入立即开始 T-004。

**错误原因**：违反"一个任务，一次报告"原则。用户可能想审查 diff、提交、交接。

**修复方式**：Report 之后始终停止。用户显式说"continue" / "next"后才继续。

---

## 8. 过度测试无关领域

**症状**：任务 acceptance 要求"test xhs.test.ts passes"。执行者运行了完整测试套件，一个无关测试失败，执行者卡在那里。

**错误原因**：acceptance 范围即任务范围。无关失败是另一个问题。

**修复方式**：按所写内容运行验收命令。如果更广泛的健全性检查发现了无关问题 → 作为观察记录，不要因此阻塞本任务。

---

## 9. SelfCheck 使用 `# it should work` 注释代替命令

**症状**：任务 acceptance 中没有可运行的检查（因为 task skill 未分解它），所以执行者添加了类似 `// verified manually` 的注释并标记 DONE。

**错误原因**：不可验证；无回归保护。

**修复方式**：如果任务 acceptance 确实没有可运行的检查（例如"config value updated"），那该 acceptance 是文件状态谓词——读取文件并以编程方式检查。如果任务确实需要人工确认，报告 DONE-PENDING-MANUAL 并等待。

---

## 10. 使用 Claude 内部 TaskCreate / TaskUpdate 作为进度模型

**症状**：impl 使用 Claude 私有任务 API 做自己的跟踪，用户在 `.claude/tasks/*.tasks.md` 中什么也看不到。

**错误原因**：基于文件的任务状态是用户可见的真实来源。内部跟踪对会话是临时的。

**修复方式**：始终追加到任务文件的 `## Status log`。内部工具可以使用，但必须同步到文件。

---

## 11. 重用状态行

**症状**：任务 T-003 失败为 BLOCKED；执行者稍后重试，将 BLOCKED 状态行编辑为 DONE。

**错误原因**：破坏审计轨迹。

**修复方式**：追加新的状态行。旧行保留。参见 `state-machine.md` 中每个任务的多条状态行。

---

## 12. 不上报测试观察

**症状**：SelfCheck 期间，执行者注意到无关领域有 3 个预先存在的测试失败。什么也没说。

**错误原因**：丢失信号。用户不知道项目有失败的测试。

**修复方式**：在状态摘要中注明："Observation: project has N pre-existing test failures in area X (not this task's responsibility)"。由用户决定。

---

## 13. 重写 spec 以匹配 impl

**症状**：impl 发现 spec 的延迟约束（p99 < 200ms）不现实。将 spec 编辑为"300ms"。

**错误原因**：impl 不是 spec 的权威。Spec 是契约。

**修复方式**：如果 impl 认为 spec 有误，发出 NEEDS_CONTEXT："constraint p99<200ms seems unachievable on current infra, local test shows ~280ms. Please confirm spec or relax constraint." 让用户修改 spec。

---

## 14. 在状态行中使用"应该"/"会"语言

**症状**：状态行写"DONE — should handle all cases correctly"。

**错误原因**："should"是推测。状态行是事实。

**修复方式**：使用过去时态的观察事实："3/3 acceptance cmds green"、"file exports match"、"curl returned 200"。

---

## 15. 跳过 DWC 的 concern 文档

**症状**：状态行显示 DONE_WITH_CONCERNS 但未列出任何 concern。

**错误原因**：`[?]` 信号没有 concern 就毫无意义。

**修复方式**：DWC 状态行必须内联包含具体的 concern，或改写为 DONE（如果实际上没有 concern）或 NEEDS_CONTEXT（如果 concern 实际上是阻塞项）。

---

## 16. 在 task 文件确认前急于实施

**症状**：用户要求规划；impl 直接跳到编码。

**错误原因**：跨 skill 边界违规。Impl 消费任务，不生产任务。

**修复方式**：如果用户尚未确认任务（通过 task skill 或临时确认），不要执行。退回到 task skill 或先请求临时确认。
