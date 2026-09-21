# Handoff: IMPLEMENT

> 生成时间: 2026-09-22T00:30:00Z | 任务: `absorb-questionnaire`

## 1. Settled Decisions (已锁定的决策)

- `to-questionnaire` 技能成功落盘至 `plugins/tinder-kit/skills/to-questionnaire/SKILL.md`，配置 `disable-model-invocation: true`。
- 完整实现了三步操典：审问接收人（Who is it going to）、审问待决缺口（What do you need back）、起草并落盘问卷（Draft & Save）。
- 确立问卷默认落盘至 `.forge/questionnaires/<slug>.md`，遵循标准 Markdown 结构（含 Purpose/From/To、Context、How to answer、带 `_Why this matters_` 与留白 `> ` 的独立单点问题、Anything else）。
- 在 `test_skills_contract.py` 中登记为 `USER_INVOKED_FLOWS` 并断言全绿。

## 2. Agreed Seams & Contracts (深接缝与行为契约)

- **Seam 1 (`plugins/tinder-kit/skills/to-questionnaire/SKILL.md`)**: PASS。合法 frontmatter、三步操典与完整问卷模板落地。
- **Seam 2 (`plugins/tinder-kit/tests/test_skills_contract.py`)**: PASS。通过结构性契约与权限断言测试。

## 3. Discovered Gotchas (隐性事实与暗坑)

- 强调单一问题单一概念，杜绝复合问题；对容易草率回答的关键决策必须附带 `_Why this matters_`，解释背后工程实现与成本差异。

## 4. Touchpoints (改动文件与边界)

- `plugins/tinder-kit/skills/to-questionnaire/SKILL.md`: 新增技能定义
- `plugins/tinder-kit/tests/test_skills_contract.py`: 登记契约断言

## 5. Next Objective (下阶段核心交付目标)

推进至 Phase 4（REVIEW），执行双轴审查与全量测试防回归背书。
