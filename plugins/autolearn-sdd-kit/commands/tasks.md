---
command: /tasks
description: 任务规划
agent: TaskPlanner
---

# /tasks

调用 **TaskPlanner**（任务规划师）进行原子级任务分解。

## 用法

```bash
/tasks <需求名>
```

**如果不传参数**，直接输出以下用法说明后返回：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /tasks 用法
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /tasks <需求名>

  将设计方案拆为原子级任务清单。
  每个 step 是一个可执行动作（精确文件/稳定锚点/验收方式）。

  产出: .claude/tasks/<需求名>.tasks.md

  前置: /design <需求名> 或 /brainstorming
  下一步: /impl <需求名>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 执行

1. 读取 `./.claude/plans/<需求名>-plan.md` 设计方案
2. 调用 **TaskPlanner** Agent
3. 进行架构分析，输出：核心模块、公共能力、依赖关系图
4. 分解任务，每个 Task：
   - 标注 `role`（frontend / backend / mobile / devops / shared）
   - 标注 `stack`（技术栈）
   - 标注 `depends_on`（依赖的 Task 列表，用于并行执行）
   - 拆分为原子级 step（每个 step 是一个可执行动作）
5. 根据任务复杂度选择 Strict atomic mode 或 Lean task mode
6. 产出 `./.claude/tasks/<需求名>.tasks.md`

## 任务详细度要求

默认要求：每个 step 都应足够明确，让执行者无需再做大幅二次规划。

### Strict atomic mode

适用于高确定性、小范围任务：
- 简单修改 → 文件路径 + 稳定锚点/必要时行号 + 具体改动
- 新建文件 → 关键结构或必要时完整代码
- 运行验证 → 精确命令 + 预期结果

### Lean task mode

适用于跨模块或较大任务：
- 写清改哪个文件/模块、做什么、如何验收
- 不强制每一步都给完整代码
- 优先用函数名、模块名、组件名等稳定锚点，避免过度依赖行号

禁止出现：TBD、TODO、"添加适当处理"、"实现 XX 功能"

## 完成后

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task Planning Complete

Total: X Tasks, Y atomic steps
Roles: frontend, backend
Parallelizable: <无依赖冲突的 Task 组；如无则写 None>

File: ./.claude/tasks/<需求名>.tasks.md

Next: /impl <需求名>              (serial, auto-detect tests)
      /impl <需求名> --no-tests   (skip tests)
      /impl <需求名> --parallel   (parallel execution)
      /review-plan <需求名>       (review plan quality)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
