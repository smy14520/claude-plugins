---
command: /design
description: 方案设计（含代码分析和访谈模式）
agent: Architect
---

# /design

调用 **Architect** 进行方案设计。

**能力**：分析代码库、访谈模式、架构设计、ADR 记录

## 用法

```bash
/design <需求描述>    # 开始设计
```

## 执行流程

```
Phase 0: Current State Analysis
  └─ Glob/Grep/Read 分析技术栈、模式、技术债务

Phase 1: Requirements Gathering（访谈模式）
  └─ AskUserQuestion 澄清需求和约束

Phase 2: Architecture Design
  └─ 遵循设计原则，应用常见模式，检查 Red Flags

Phase 3: ADR Documentation
  └─ 记录每个技术决策的 Context/Decision/Consequences/Alternatives

产出: ./.claude/plans/<需求名>-plan.md
```

## 架构分析能力

| 分析项 | 命令示例 |
|--------|----------|
| 技术栈 | `Glob "package.json\|requirements.txt"` |
| 状态管理 | `Grep "createContext\|createStore\|useStore"` |
| 路由 | `Grep "useRouter\|useNavigate"` |
| API 层 | `Grep "axios\|fetch\|gql"` |
| 样式 | `Grep "tw-\|styled(\|import.*css"` |
| 技术债务 | `Grep "TODO\|FIXME\|any\|@ts-ignore"` |

## 产出文件结构

```
## 0. Current State Analysis
## 1. 需求理解
## 2. 非功能需求
## 3. Spec 规范
## 4. 架构设计
## 5. 技术决策记录 (ADR)
## 6. 实现路径
## 7. 验收标准
## 8. Red Flags 检查
## 9. 风险与建议
```

## 完成后

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 设计方案已完成
文件: ./.claude/plans/<需求名>-plan.md

下一步: /tasks <需求名>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
