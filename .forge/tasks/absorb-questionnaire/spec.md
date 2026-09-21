# 吸收反向决策问卷技能 to-questionnaire

## Goal

在 tinder-kit 中吸收并现代化改造反向决策问卷技能 to-questionnaire。当开发者面临无法独自裁决的跨团队/跨角色决策（如产品边界、法务合规、架构审批）时，提供“审问发送对象与认知缺口（Grill the send, not the subject）”的高效提炼引擎，自动生成格式严谨、可异步填写的 Markdown 决策问卷，统一存放于 `.forge/questionnaires/<slug>.md`。

## Latent Assumptions Exposed

- 假设 1: 技能定位为 User-invoked 面向开发者的主航道流，配置 `disable-model-invocation: true`；在 `/develop` 或 `/wayfinder` 遇到非当前开发者所能决定的阻断性分歧时，编排器可提议调用本技能。
- 假设 2: 问卷产物默认落盘在 `.forge/questionnaires/<slug>.md`，保持项目根目录整洁，并在终端显式输出文件路径与预览，方便用户复制到 Slack/邮件中异步发送。
- 假设 3: 操典严格遵循 Matt Pocock 的三步法（Who is it going to / What do you need back / Write the questionnaire），确保每个问题单构思、附带 answer stub 与必要的影响说明（why this matters）。

## Agreed Seams

- **Seam 1**: `plugins/tinder-kit/skills/to-questionnaire/SKILL.md`
  - 预期行为: 具备合法 frontmatter (`name: to-questionnaire`, `disable-model-invocation: true`)，规范三步访谈操典与标准问卷文档模板，清晰定义 Purpose、Context、How to answer、分组问题清单与留白 answer stub。
  - 验证命令/用例: `pytest plugins/tinder-kit/tests/test_skills_contract.py`
- **Seam 2**: `plugins/tinder-kit/tests/test_skills_contract.py`
  - 预期行为: 在 `USER_INVOKED_FLOWS` 注册集合中纳入 `"to-questionnaire"`，通过自动化契约断言。
  - 验证命令/用例: `pytest plugins/tinder-kit/tests/test_skills_contract.py`

## Empirical Findings

- 无

## Out of Scope

- 不内置任何外部表单 SaaS（如飞书问卷、Google Forms）的在线 API 发布，纯粹交付标准自包含 Markdown 文档（用户确认）
