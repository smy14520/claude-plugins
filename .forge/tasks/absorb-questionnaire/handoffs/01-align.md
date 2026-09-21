# Handoff: ALIGN

> 生成时间: 2026-09-22T00:00:00Z | 任务: `absorb-questionnaire`

## 1. Settled Decisions (已锁定的决策)

- 技能命名确定为 `to-questionnaire`，与 Matt Pocock 官方原版保持一致。
- 权限定位为 User-invoked（`disable-model-invocation: true`）。
- 问卷产物存放于 `.forge/questionnaires/<slug>.md`。
- 核心哲学：**Grill the send, not the subject**（当开发者缺乏答案时，不要拷问主题本身，而是拷问接收方角色与待补齐决策缺口）。

## 2. Agreed Seams & Contracts (深接缝与行为契约)

- **Seam 1**: `plugins/tinder-kit/skills/to-questionnaire/SKILL.md`（完整三步操典与标准问卷 Markdown 模板）
- **Seam 2**: `plugins/tinder-kit/tests/test_skills_contract.py`（在 `USER_INVOKED_FLOWS` 注册并测试通过）

## 3. Discovered Gotchas (隐性事实与暗坑)

- 避免把问卷写成冗长的背景交代：接收方往往时间宝贵，Context 限制为一段，重点在有编号、带留白 answer stub（`> `）的具体单点决策。

## 4. Touchpoints (改动文件与边界)

- `plugins/tinder-kit/skills/to-questionnaire/SKILL.md`: 新增技能定义
- `plugins/tinder-kit/tests/test_skills_contract.py`: 登记契约断言

## 5. Next Objective (下阶段核心交付目标)

在 Phase 3 完成 `to-questionnaire` 技能操典与测试断言编写，运行 `pytest` 验证通过。
