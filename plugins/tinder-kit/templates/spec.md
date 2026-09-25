# {title}

## Problem & Goal

- **Problem**：{problem}
- **Goal**：{goal}

## Acceptance Criteria（业务行为真值）

<!-- 站在消费者/调用方视角，列出本垂直切片对外承诺的 2~4 条可证伪行为真值断言 -->
- [ ] **AC-1**：{ac_1}
- [ ] **AC-2**：{ac_2}

## Implementation Decisions（已定技术与架构决断）

<!-- 锁定访谈中已达成共识的技术决断，防止子 Agent 在编码时擅自漂移或推翻。避免粘贴大段实现代码 -->
- **修改模块与接口**：{decision_modules}
- **数据结构与协议**：{decision_schema}
- **架构约束与选型**：{decision_architecture}

## Testing Decisions & Seams（物理验证契约）

<!-- 明确测试策略与代码库现存标杆用例，绑定硬性验证命令 -->
- **Prior Art（测试标杆）**：{prior_art_test}（子 Agent 参照此测试文件的 Assert 与 Mock 风格）
- **Agreed Seams**：
  - **Seam 1**：`{seam_1_signature}`
    - 覆盖验收项：AC-1, AC-2
    - 验证命令/用例：`{seam_1_test}`

## Latent Assumptions Exposed（显影的隐性假设）

<!-- 动手前说明预设的技术事实，防止隐性假设导致返工 -->
- 假设 1：{assumption_1}
- 假设 2：{assumption_2}

## Empirical Findings（原型探索实证）

<!-- 原型探索（prototype）实证结论，无则写“无” -->
- 无

## Out of Scope（明确排除的范围）

<!-- 明确不做的范围，必须经用户确认，防止范围蔓延 -->
- {out_of_scope_item}（用户确认）
