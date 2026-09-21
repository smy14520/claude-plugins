# Handoff: ALIGN

> 生成时间: 2026-09-21T00:00:00Z | 任务: `absorb-research`

## 1. Settled Decisions (已锁定的决策)

- `research` 技能定位为面向开发者的主航道流（User-invoked），配置 `disable-model-invocation: true`。
- 调研工作区采用独立目录 `.forge/research/<topic>/`，以 index-first 组织 `raw/` 与 `notes/`。
- 外部资料必须显式标记出处 URL 与查证日期（`查证于 YYYY-MM-DD（来源：URL）`）。
- 绝非所有资料都进 Wiki：仅通用系统能力拓扑进 `.forge/wiki/research/<topic>.md`、反直觉外部暗坑进 `.forge/wiki/gotcha/`、选型结论进 `.forge/wiki/decision/`。不易抓取的关键端点与真实 payload 样例在工作区与 Wiki 中均作为宝贵凭据妥善保留。

## 2. Agreed Seams & Contracts (深接缝与行为契约)

- **Seam 1**: `plugins/tinder-kit/skills/research/SKILL.md`（完整操典，包含工作区范式、出处纪律、载荷样本留存与 Wiki 晋升准则）
- **Seam 2**: `plugins/tinder-kit/tests/test_skills_contract.py`（在 `USER_INVOKED_FLOWS` 注册并测试通过）

## 3. Discovered Gotchas (隐性事实与暗坑)

- 避免一刀切禁止记录 API 字段：很多政企或封闭系统文档外部抓取极难，必须允许保留关键 payload 样例与核心端点，绝不能为了“简洁”把关键对接信息丢弃。
- 必须严格配置 `disable-model-invocation: true`，防止模型在普通任务执行过程中未经人类同意擅自大范围抓取外部网页，造成上下文爆炸与停顿。

## 4. Touchpoints (改动文件与边界)

- `plugins/tinder-kit/skills/research/SKILL.md`: 新建技能定义
- `plugins/tinder-kit/tests/test_skills_contract.py`: 登记测试并验证契约

## 5. Next Objective (下阶段核心交付目标)

由子 Agent（`forge-impl`）在干净上下文里创建 `plugins/tinder-kit/skills/research/SKILL.md`，并在 `test_skills_contract.py` 中更新断言，运行 `pytest` 跑绿。
