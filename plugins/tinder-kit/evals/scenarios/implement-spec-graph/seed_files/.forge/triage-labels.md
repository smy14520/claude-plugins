# Triage Labels

工程技能基于五种标准分流角色定义工作。本文件将这些抽象角色映射到本仓库 Issue Tracker 中使用的真实标签字符串。

| 标准角色名称 | 仓库中实际标签 | 语义与流转说明 |
| :--- | :--- | :--- |
| `needs-triage` | `needs-triage` | 刚提交的新需求/缺陷，维护者需要评估分流 |
| `needs-info` | `needs-info` | 信息不足，正在等待提单方提供补充事实 |
| `ready-for-agent` | `ready-for-agent` | 规格与 Seams 已经敲定，准备好由 Agent 全自动编码实现 |
| `ready-for-human` | `ready-for-human` | 涉及高风险单向门决策或商业考量，必须由人类亲自实现 |
| `wontfix` | `wontfix` | 经裁决不予实现或明确 Out of Scope |

当技能提及某个角色时（如“为已就绪的工单打上 AFK-ready 标签”），使用上表对应的一列字符串。
你可以随时编辑第二列以匹配你们团队实际的标签习惯。
