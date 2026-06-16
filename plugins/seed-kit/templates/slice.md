# S-001 <标题>

## 交付面

<!-- 闭集：backend-domain / api / web-ui / e2e / compliance / infra。
     只声明本 slice 实际交付的面；验证面必须覆盖这里每一项。 -->

- backend-domain

## 验收

<!-- 对应哪几条 AC；必要时展开 Given/When/Then 细节与失败路径 -->

## 验证面

<!-- 验证项 = [kind][surface] target：kind 表示谁判定通过，surface 表示覆盖哪个交付面。
  - [assert][backend-domain] `命令`  命令本身是会失败的断言（测试套件 / 契约回放 / Playwright spec）。
                                      seed 真实执行它，exit 0 才算 passed；裸 curl/echo 这类“跑过就算过”
                                      的烟雾命令会被标记警告，且不能覆盖交付面。
  - [judge][web-ui] 描述             由独立 agent（fresh session，生成者≠验证者）看渲染产物按 AC rubric 裁决，
                                      用 `seed run-check --judge ... --verdict pass|fail --trace ... --artifact <截图>` 落盘。
                                      web-ui 整体体验用高标开放 rubric（设计质量+原创性，打低“通用 AI 味”），非功能清单。
  - [human][compliance] 描述         真人 stakeholder 签收（合规、备案、本质上不可自动化），
                                      用 `seed run-check --human ... --note ... --by ...` 记录。
  旧式裸 `命令` 视为 [assert]，[manual] 视为 [human]，仍可解析；但没有 surface 标签时不覆盖交付面。
  原则：每个交付面都要被验证面覆盖；human 不能替代 backend-domain/api/web-ui/e2e/infra。 -->

- [assert][backend-domain] `<会失败的断言命令>`
