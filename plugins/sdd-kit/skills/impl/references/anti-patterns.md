# Impl 反模式

只保留需要语义判断的反模式；可机械校验的违规（无证据标 done、手写 task.json、impl 期间改 prd.md、第二套执行计划）已由 mark-slice gate、record-impl-result 校验、arbor_guard hook 和 validation 直接拒绝，不在此重复。

## 静默做设计决策以解除阻塞

PRD 对承重决策（性能预算、重试 / 超时、权限边界、数据模型、版本兼容等）有歧义时，不要自行拍板。发出 NEEDS_CONTEXT，并引用具体来源。

## 将 BLOCKED 伪装为 DONE_WITH_CONCERNS

DONE_WITH_CONCERNS 只有在功能代码兑现 PRD 承诺、仅验证手段受限时才成立。核心功能无法判断就是 BLOCKED；信息缺失就是 NEEDS_CONTEXT。

## 在实现中夹带清理工作

保持实现聚焦于当前 package PRD scope。相邻清理另起需求或回 brainstorm 修改 PRD。

## 过度重做 brainstorm

impl 可以读取 PRD 和实际代码状态，但目标是理解当前 scope，不是重新判断产品方向。认为上游文档有误时发 NEEDS_CONTEXT，或留给 review 标记 BRAINSTORM_DRIFT。

## 把 DONE 当成 delivered

DONE 只表示当前 package PRD scope 的证据结算通过。是否 delivered 还需要 review / 用户验证 / merge / release 事实。
