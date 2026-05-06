# Impl 反模式

## 未运行 self-check 即声称 DONE

必须执行从 PRD 推导出的 self-check。无法运行则是 BLOCKED / NEEDS_CONTEXT，而非 DONE。

## 静默做设计决策以解除阻塞

PRD 对承重决策（性能预算、重试 / 超时、权限边界、数据模型、版本兼容等）有歧义时，不要自行拍板。发出 NEEDS_CONTEXT，并引用具体来源。

## 将 BLOCKED 伪装为 DONE_WITH_CONCERNS

DONE_WITH_CONCERNS 只有在 self-check 通过时才成立。否则就是 BLOCKED 或 NEEDS_CONTEXT。

## 修改需求定义使其通过

impl 不得编辑 PRD 的需求内容或手写 task.json。若上游定义有问题，返回 NEEDS_CONTEXT。

## 在实现中夹带清理工作

保持实现聚焦于当前 package PRD scope。相邻清理另起需求或回 brainstorm 修改 PRD。

## “运行了测试”但不看输出

检查退出码和输出，不做表面通过。

## 在 slice 之间停下来等用户确认

PRD 定稿后才进入 impl；执行阶段应连续推进所有 Slices。只有 NEEDS_CONTEXT 或 BLOCKED 才停止。

## 过度重做 brainstorm

impl 可以读取 PRD 和实际代码状态，但目标是理解当前 scope，不是重新判断产品方向。

## 重写 PRD 以匹配 impl

impl 不是 PRD 的权威。若认为上游文档有误，发 NEEDS_CONTEXT，或留给 review 标记 BRAINSTORM_DRIFT。Impl 不修改 PRD，slice 进度通过 `sdd-arbor mark-slice` 写入 `task.json`。

## 把 DONE 当成 delivered

DONE 只表示当前 package PRD scope self-check 通过。是否 delivered 还需要 review / PR / merge / release 事实。

## 用第二套执行计划替代 Slices

不要创建 execution plan、status.md 或 TODO 文件。`## Slices` 是断点续作提示；task.json 是 lifecycle 状态源。

## self-check 不记录依据

`record-impl-result` 必须记录 self-check 来源、命令/谓词和结果，供 review 审计。
