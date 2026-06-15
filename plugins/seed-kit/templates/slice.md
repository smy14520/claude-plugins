# S-001 <标题>

## 验收

<!-- 对应哪几条 AC；必要时展开 Given/When/Then 细节与失败路径 -->

## 验证

<!-- 三类验证（封闭词汇），按"谁判定它对"选择：
  - [assert] `命令`   命令本身是会失败的断言（测试套件 / 契约回放 / Playwright spec）。
                       seed 真实执行它，exit 0 才算 passed；裸 curl/echo 这类"跑过就算过"
                       的烟雾命令会被标记警告——它们只证可达，不证语义。
  - [judge] 描述       由独立 agent（fresh session，生成者≠验证者）按 AC rubric 裁决，
                       用 `seed run-check --judge ... --verdict pass|fail --trace ...` 落盘。
                       用于难以机械断言的语义/UI/手感。
  - [human] 描述       真人 stakeholder 签收（品味、合规、本质上不可自动化），
                       用 `seed run-check --human ... --note ... --by ...` 记录。
  旧式裸 `命令` 视为 [assert]，[manual] 视为 [human]，仍可用。
  原则：assert 优先；能用断言就别用 judge，能 judge 就别堆 human。 -->

- [assert] `<会失败的断言命令>`
- [judge] <按 rubric 裁决的描述，注明 rubric 位置>
- [human] <真人签收项>
