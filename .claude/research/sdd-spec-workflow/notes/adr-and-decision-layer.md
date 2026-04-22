# ADR 与决策记录层

## 当前结论

ADR 类样本说明：**feature spec 并不能天然替代决策记录**。当问题是“这次需求要做什么、怎么拆、怎么验收”时，spec 很合适；但当问题是“我们长期采用什么原则、为什么选择这个方向、以后如何回溯”时，ADR 更合适。

OpenSCD 的实践又补充了一个有价值的点：**draft / review / accepted 不一定要额外造系统，可以直接借用 PR 生命周期。**

## 来源

- `../raw/ext-adr-and-async-pr.md`

## 这对需求意味着什么

对于当前 research → spec → task → impl 工作流，ADR 的价值主要有三类：

1. **承接横切决策**
   - 例如：什么时候必须进入 spec、spec 应保留哪些字段、review 应审什么
   - 这些更像 workflow constitution / decisions，而不是单 feature spec

2. **保留 why，而不是只保留 what**
   - spec 更适合冻结当前任务的 contract
   - ADR 更适合记录“为何这么设计 workflow”

3. **连接治理与自动化**
   - ADR 仓库里的 fitness functions / decision guardrails 给出一个方向：决策文件未来可以变成 PR/CI 守卫

4. **与“行为规则层”分工**
   - `forrestchang/andrej-karpathy-skills` 这类单文件原则包说明：有些问题更适合放在全局行为约束层，例如不要瞎猜、保持简单、做外科式修改、用可验证目标驱动执行
   - 但它不能代替 task 状态、spec 工件和 handoff 结构，因此更适合作为 workflow 的宪法层，而不是 workflow 本身

## 当前判断

- 如果当前项目只是把 feature 做完，ADR 不是必需。
- 但如果当前项目是在设计一套长期 workflow，那么至少要考虑是否保留一层“workflow decisions”记录。
- 这一层不一定叫 ADR，但需要与 feature spec 区分。

## 仍未解决的问题

- workflow 级决策是放进 CLAUDE.md / rules，还是单独 decisions/ADR？
- “进入 spec 的判定规则”这类内容，是否适合成为长期 decision artifact？
- 是否需要把 ADR/decision 与 PR review、lint、脚本检查连接起来？

## 相关笔记

- `ai-spec-first-toolkits.md`
- `rfc-kep-and-doc-gates.md`
- `workflow-design-principles.md`
