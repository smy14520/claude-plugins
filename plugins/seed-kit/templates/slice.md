# S-001 <标题>

## 交付面

<!-- 参考词汇表（非封闭）：backend-domain / api / web-ui / e2e / compliance / infra；项目可用任意面名（游戏 gameplay、CLI cli-dx 等）。
     只声明本 slice 实际交付的面；验证面必须覆盖这里每一项。 -->

- backend-domain

## 验收

<!-- 对应哪几条 AC；必要时展开 Given/When/Then 细节与失败路径 -->

## 验证面

<!-- 验证项 = 验收义务（obligation）：`[kind][surface] <obligation-id>: <可观测行为>`。
     kind 表示谁判定通过（assert/judge/human），surface 表示覆盖哪个交付面（可多个，逗号分隔）。
     obligation-id 是这条义务的 slug（可带 AC-N 标签作 review 对账线索，helper 不解析 AC 全集）；
     冒号后是**可观测行为**——能观察、能判定对错。命令**不**写在这里，由 impl 用
     `seed run-check --obligation <id> -- <会失败的断言命令>` 真实执行并绑定到义务。
  - [assert][backend-domain] <id>: <行为>  命令本身是会失败的断言（测试套件/契约回放/Playwright spec）。
          run-check 真实执行，exit 0 才 passed；裸 curl/echo 这类烟雾命令对非 compliance 面会被硬挡。
  - [judge][web-ui] <id>: <行为>           由独立 agent（agent team 的 reviewer 或 subagent，生成者≠验证者）看渲染产物按 AC rubric
          裁决，用 `--obligation <id> --verdict pass|fail --trace ... --artifact <截图>` 落盘。
          web-ui 整体体验用高标开放 rubric（设计质量+原创性，打低“通用 AI 味”），非功能清单。
  - [human][compliance] <id>: <行为>        真人 stakeholder 签收（合规、备案、本质不可自动化），
          用 `--obligation <id> --note ... --by ...` 记录。
  旧式裸 `命令` 视为 [assert]，[manual] 视为 [human]，仍可解析；但没有 surface 标签时不覆盖任何交付面。
  原则：每个交付面都要被验证面覆盖；human 不能替代 backend-domain/api/web-ui/e2e/infra。 -->

- [assert][backend-domain] <obligation-id>: <可观测行为，能失败>
