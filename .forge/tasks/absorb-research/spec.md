# 吸收并升级外部资料调研技能 research

## Goal

在 tinder-kit 中吸收并现代化改造外部资料调研技能 research，确立基于 `.forge/research/<topic>/` 的 index-first 独立工作区协议、强制的「出处与查证日期」锚定规范、关键载荷/端点样本保留标准、以及向三级记忆（.forge/wiki/）进行高质量知识晋升的完整闭环。

## Latent Assumptions Exposed

- 假设 1: research 属于面向开发者的高阶主航道（User-invoked），配置 `disable-model-invocation: true`，由用户主动输入 `/research` 触发；当 `/develop` 遇到外部技术黑盒时可向用户提议先做 research。
- 假设 2: 工作区必须任务与项目自包含，落盘在 `.forge/research/<topic>/`（含 `index.md` 导航、`raw/` 原始证据、`notes/` 提炼笔记）。
- 假设 3: 外部对接资料严格要求保留出处 URL 与当前查证日期，允许并鼓励收录不易再次抓取的核心 API 端点与请求/响应 payload 样例；调研收尾可将通用系统认知晋升至 `.forge/wiki/research/`、暗坑晋升至 `gotcha/`。

## Agreed Seams

- **Seam 1**: `plugins/tinder-kit/skills/research/SKILL.md`
  - 预期行为: 遵循 Matt Pocock 技能解耦哲学与 tinder-kit 规范，携带 `name: research` 与 `disable-model-invocation: true`；定义 index-first 工作区布局；规范 URL+日期出处标注与关键契约样本留存；定义向 `.forge/wiki/`（research/gotcha/decision）的知识晋升流。
  - 验证命令/用例: `pytest plugins/tinder-kit/tests/test_skills_contract.py`
- **Seam 2**: `plugins/tinder-kit/tests/test_skills_contract.py`
  - 预期行为: 在 `USER_INVOKED_FLOWS` 注册集合中纳入 `"research"`，断言 frontmatter 合法性、权限隔离与禁用模型自主调用。
  - 验证命令/用例: `pytest plugins/tinder-kit/tests/test_skills_contract.py`

## Empirical Findings

- 无

## Out of Scope

- 不内置复杂的网络爬虫或外部抓取中间件（依赖环境原生的 WebSearch / WebFetch / curl 即可）（用户确认）
- 不修改 plugins/seed-kit 下的旧版代码（用户确认）
