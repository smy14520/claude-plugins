# 四状态机

Impl 对单个 package-local T-xxx 报告且仅报告以下四种状态之一。本文件给出定义、退出标准和转换规则。Package 顶层状态由 `task.json` 聚合多个 T-xxx 得出；单个 DONE 不等于 package branch/worktree/PR 完成。

---

## DONE

**含义**：任务完成。所有验收标准通过。无已知妥协或遗留问题。

### 退出标准（全部必须满足）

- `acceptance:` 中的每条命令均已执行并返回成功
- `acceptance:` 中的每个文件状态谓词均已验证
- 无已知偏离 task-local context 的情况
- 代码自洽（本任务无残留 TODO）

---

## DONE_WITH_CONCERNS

**含义**：验收通过，但执行者做了一项值得上报的妥协。

### 何时使用

- 使用了满足验收但并非最干净方案的变通手段
- 跳过了任务备注中提到的可选改进
- 引入了未来读者应知晓的小额技术债

---

## NEEDS_CONTEXT

**含义**：执行者遇到 task-local 信息缺失或冲突，被迫做出设计决策。拒绝猜测。

### 何时使用

- task 说 X，PRD 背景暗示 Y，二者冲突
- acceptance 引用了不存在的文件/命令
- 缺少影响行为的具体值（TTL、重试次数、URL、枚举选择）
- 存在两种合理实现方案且 task 未冻结选择
- `ready-check` 中的 blocker 表明该任务尚未真正 ready
- 任务或上游文档中仍有与本任务直接相关的 `<TODO-DECIDE>` / `<TBD>`

### 必须输出

- **受阻于**：一句话概述歧义所在
- **所需信息**：能解除阻塞的具体问题
- **歧义来源**：位于 PRD / task / source 的何处
- **建议解决方案**：对 PRD 或 task 做什么变更可解除阻塞
- **代码状态**：no code changes 或 partial

---

## BLOCKED

**含义**：环境或外部因素阻止任务执行，与设计歧义无关。

### 何时使用

- 依赖未安装，缺少二进制文件
- 外部服务不可达
- Migration 因基础设施原因失败
- 机器级别的权限 / 认证问题
- 上游依赖任务尚未完成

---

## 升级规则

如果一个任务经历 NEEDS_CONTEXT / BLOCKED 3 次以上，提示用户：
- task 可能拆分不当（回 task）
- 或 PRD 仍有关键歧义（回 brainstorm 更新 `prd.md`）
- 或 research 还不够（回 research）
