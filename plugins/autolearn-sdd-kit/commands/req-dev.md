---
command: /req-dev
description: SDD 规范驱动开发流程编排
---

# /req-dev

SDD 规范驱动开发的**流程编排命令**，负责意图识别和 Agent 调度。

## 用法

```bash
/req-dev                      # 查看进行中的需求
/req-dev <需求描述>            # 开始新需求
/req-dev 继续 <需求名>         # 断点续做
```

## 流程编排

```
1. 识别项目: `project = basename(pwd)`
/req-dev <需求描述>
    │
    ├─ 1. 意图识别
    │      判断：新需求 / 继续 / 修bug / 查询
    │
    ├─ 2. 调用 ContextDetective（自动）
    │      检索规则、经验、模块索引
    │      输出上下文报告
    │
    ├─ 3. 调用 Architect（/design）
    │      设计 Spec & Plan
    │      产出: ~/.claude/context/plans/<project>/<需求名>-plan.md
    │      ⏸️ 【检查点】等待人工确认（review_status: pending → approved）
    │
    ├─ 4. 调用 TaskPlanner（/breakdown）
    │      分解任务清单
    │      产出: ~/.claude/context/tasks/<project>/<需求名>.tasks.md
    │      ⏸️ 【检查点】等待人工确认（review_status: pending → approved）
    │
    ├─ 5. 调用 Developer（/do）
    │      根据 Task 的 role 调度专业开发者
    │      默认连续执行，不中断
    │      产出: 代码
    │
    └─ 6. 调用 KnowledgeEngineer（/extract-experience）
           沉淀经验
           产出: ~/.claude/context/experience/<project>/<名称>.md
```

## 检查点机制

设计和任务分解阶段需要人工审阅确认，确保方向正确。

### 状态流转

| 阶段 | 文件 | 状态字段 |
|------|------|----------|
| /design | `~/.claude/context/plans/<需求名>-plan.md` | `review_status: pending → approved` |
| /breakdown | `~/.claude/context/tasks/<需求名>.tasks.md` | `review_status: pending → approved` |

### 确认方式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 设计方案已完成，请审阅

您可以：
- 输入 "确认" 或 "ok" → 继续下一步
- 输入 "修改: <意见>" → 修改方案后重新审阅
- 输入 "重做" → 从头重新设计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 执行阶段（/do）

- **默认**：连续执行所有任务，不中断
- **逐步确认**：用户说"逐步确认"或在 tasks 文件设置 `confirm_each: true`

## 意图识别

| 输入 | 意图 | 执行 |
|------|------|------|
| 无参数 | 查看需求 | 列出进行中的 tasks 文件 |
| `继续 xxx` | 断点续做 | 读取 tasks 文件，从未完成处继续 |
| 含 "修复/bug" | fix_bug | 跳过 design/breakdown，直接 do |
| 其他 | 新需求 | 完整流程 |

## 断点续做

```bash
/req-dev 继续 GitHub-SSO登录
```

1. 读取 `~/.claude/context/tasks/GitHub-SSO登录.tasks.md`
2. 找到第一个 `- [ ]` 的小点
3. 调用 Developer 从该小点继续
