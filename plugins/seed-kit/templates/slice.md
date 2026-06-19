# S-001 <标题>

## 交付面

<!-- 参考词汇表（非封闭）：backend-domain / api / web-ui / e2e / compliance / infra；项目可用任意面名（游戏 gameplay、CLI cli-dx 等）。
     只声明本 slice 实际交付的面；验证面必须覆盖这里每一项。 -->

- backend-domain

## 验收

<!-- 对应哪几条 AC；必要时展开 Given/When/Then 细节与失败路径 -->

## 验证面

<!-- 验证项 = 验收义务（obligation）：`[kind][surface] <obligation-id>: <可观测行为>`。
     kind = assert / judge / human（详见 conventions / DESIGN.md）；surface = 覆盖哪个交付面。
     命令**不**写在这里，由 impl 用 `seed run-check --obligation <id> -- <会失败的断言命令>` 真实执行并绑定到义务。
     judge 可用 legacy verdict，也可用项目 rubric + score-file 让 helper 计算 verdict；分数维度与门槛来自项目。
     原则：每个交付面都要被验证面覆盖；human 覆盖可断言交付面是设计气味，但 helper 不机械禁止，由项目规则与 review 查验证降级。 -->

- [assert][backend-domain] <obligation-id>: <可观测行为，能失败>
