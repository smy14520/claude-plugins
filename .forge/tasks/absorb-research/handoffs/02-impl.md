# Handoff: IMPLEMENT

> 生成时间: 2026-09-21T15:10:00Z | 任务: `absorb-research`

## 1. Settled Decisions (已锁定的决策)

- `research` 技能落地于 `plugins/tinder-kit/skills/research/SKILL.md`，配置 `disable-model-invocation: true`，作为 User-invoked 流程。
- 工作区采用独立的 `.forge/research/<topic>/`，严格执行 index-first 规范：`index.md` + `raw/` + `notes/`。
- 确立出处纪律：强制要求标明 `查证于 YYYY-MM-DD（来源：<URL>）`。
- 确立外部契约样本留存：针对不易再次抓取的接口，重点保留核心端点与请求/响应 payload 样本。
- 确立 Wiki 知识晋升流：全局认知晋升至 `.forge/wiki/research/<topic>.md`，暗坑晋升至 `gotcha/`，选型晋升至 `decision/`。

## 2. Agreed Seams & Contracts (深接缝与行为契约)

- **Seam 1 (`plugins/tinder-kit/skills/research/SKILL.md`)**: PASS。合法 frontmatter、工作区规范、四项执行纪律与退出准则全部就绪。
- **Seam 2 (`plugins/tinder-kit/tests/test_skills_contract.py`)**: PASS。纳入 `USER_INVOKED_FLOWS` 并通过自动化契约测试。

## 3. Discovered Gotchas (隐性事实与暗坑)

- 必须对外部不易直接获取的接口样本给予明确许可与倡导，避免模型过度追求形式上的简短而把后续编码必须依赖的 payload 细节删掉。

## 4. Touchpoints (改动文件与边界)

- `plugins/tinder-kit/skills/research/SKILL.md`: 新建技能操典
- `plugins/tinder-kit/tests/test_skills_contract.py`: 登记并断言技能契约

## 5. Next Objective (下阶段核心交付目标)

推进至 Phase 4（REVIEW），执行双轴代码审查与防回归背书。
