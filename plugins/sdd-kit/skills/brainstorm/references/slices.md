# Slices

PRD 定稿时必须包含 `## Slices` 段,按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多、切片最精准。

## 切分原则:独立可验证小单元

每个 slice 是一个**独立可验证的小单元**——不是某层动作的完成。可验证的对象可以是:

- **契约**:API / 函数 / 协议的输入输出约定(`POST /api/orders` 创建 pending 订单且 `GET` 返回该订单)
- **功能**:用户 / 调用方可感知的端到端能力(用户能购买课程并立即学习)
- **行为**:不变量、状态转换、对比等价性(支付成功后 enrollment 自动建立;重构后旧测试 + 对比测试都通过)
- **触发链**:状态机 lifecycle 的某次转换或事件回调链(沙盒回调触发 order pending → paid)

判定:写完一条 `完成标志` 后问自己——**"如果只完成这一个 slice 就停下来,系统是否得到了一个可独立验证的新契约 / 功能 / 行为?"** 不能 → 这是 work,合并或重写。

### 反模式:按层切

❌ work-driven(按技术层切,集成债积累):

```
S-001: 数据 schema 与 migration
S-002: Service 层 CRUD 函数
S-003: API endpoint 注册
S-004: 集成测试
```

S-001 / S-002 / S-003 完成时都"看起来对",末期 S-004 才发现 schema 缺字段、API 设计不匹配,集成债爆发。

✅ 按可验证小单元切(契约 / 行为驱动):

```
S-001: 创建 todo 后能查询到(最简 schema + 创建 + 查询 + e2e)
S-002: todo 状态可在 open / done 间流转(扩展 schema status + 状态转换 e2e)
S-003: 按状态筛选 todo(查询能力 + e2e)
```

每个 slice 完成时有可独立验证的产物,集成持续偿还。

### Walking skeleton 优先

第一个 slice 通常是 walking skeleton——穿透足够的层让"可验证小单元"立得住:

- 端到端跑通最简 happy path(框架 + DB + auth + 一个 endpoint + e2e test)
- 或最简契约(`POST /api/X` 写入 → `GET` 读取 e2e 通)

后续 slice 站在 skeleton 之上,各自补充某个契约 / 功能 / 行为 / 状态转换。这样:

- 第一 slice 的工作量集中在"穿透栈"而非"完整功能",可控
- 后续 slice 粒度均匀(每个一个可验证单元)
- 集成债零(从第一 slice 就 e2e 通)

## 护栏:避免退化

独立可验证小单元有三个常见退化路径,显式封住:

### 1. "有测试"不等于独立可验证小单元

单元测试覆盖一个内部函数,但 consumer 还没接上 → 仍是 work,只是披了测试皮。

判断:**下一个 slice 能直接依赖本 slice 产出的契约 / 行为 / 状态吗?** 不能 → 合并或重写。

- ❌ `S-001: OrderService.create 函数 + unit test`(没人用,done 时系统无可依赖产物)
- ✅ `S-001: POST /api/orders 创建 pending order + GET /api/orders/{id} 返回该订单`(consumer 侧有观测点)

### 2. API 契约 slice 必须写 consumer 侧验证

"`POST /api/orders` 返回 201" 只是生产侧,不完整。必须有消费侧可观测的验证:

- ✅ `POST /api/orders` 返回 201 + `GET /api/orders/{id}` 返回该订单(同层 API consumer)
- ✅ `POST /api/orders` 返回 201 + 前端订单列表显示该订单(跨层 consumer)

只有生产侧的 API slice 等同纯后端横切,违反第 1 条。

### 3. Walking skeleton 用真实领域最薄路径

项目已有领域(课程、订单、用户)→ 第一 slice 用真实领域薄路径(如"课程列表 e2e 通"),**不要默认 `/api/ping` + placeholder page**——这是 LLM 对 "walking skeleton" 一词的训练数据刻板印象,不是 walking skeleton 的本意。

仅当项目完全没有任何领域锚点(全新工具库首个 slice、纯框架脚手架)时,才允许用 placeholder endpoint 作为 walking skeleton。

## 写法

每个 slice 用 `### S-NNN: <标题>` 起头,body 用 `- 字段:值` 形式给出。**slice 涉及就写,不涉及就整条省略**,不写 N/A、不留占位。不分存量 / 新项目:是否写某字段只看这个 slice 的实际范围。

### 必填

- `完成标志`:一句话描述**完成后多了什么可独立验证的契约 / 功能 / 行为**,不是某层动作的完成。每个 slice 都写,没有例外。
  - ❌ work:"schema 已建"、"function 已实现"、"路由已注册"
  - ✅ 可验证小单元:"创建 user-1 后 `GET /users/u1` 返回正确数据"、"调用 `X(input)` 返回 `Y` 且测试通过"、"order 状态 pending → paid 后 enrollment 自动建立"

### 按需

- `数据 / schema`:动到数据结构、表、文件格式、模型输入输出或 migration 时写。标注 `[new]` / `[existing]`;有 artifact 时指向具体位置。
- `代码锚点`:动到或新建模块、文件、接口、页面、命令、子系统或 pipeline 时写。标注 `[new]` / `[existing]`;UI、外部集成、权限变更等都归此字段。
- `测试`:Testing strategy 为核心路径 / TDD 时写(覆盖路径 / 边界或 test 文件名);最小验收档可省。

## 完成标志 vs Acceptance Criteria

- **AC**(PRD 顶层 `## Acceptance Criteria`)是**用户视角**的整体验收:"能创建账户并查看月度统计"。
- **完成标志**是每 slice 的**可独立验证产物**:"账户 API 返回 201 + DB 记录已写入 + `GET /accounts/u1` 返回该记录"。

定稿时每条 AC 应能追溯到 1 个或多个 slice 的完成标志组合。

## 粒度

由可验证性决定:完成后能用一两句话说清楚"怎么验证"。一个 slice 需要列举 5 个以上独立功能才能描述清楚就太粗,应该拆。slice 数量没有上限。

顺序反映**价值与依赖**:第一个 slice 通常是 walking skeleton(穿透栈让后续 slice 都有挂靠);后续 slice 各自补充某个契约 / 功能 / 行为 / 状态转换。**避免按层排列**(先基建 → 再核心 → 再边缘 → 最后验收)——这种排列下 90% 的 slice 完成时无法独立验证,集成债到末期才爆发。

## 示例

### 小需求(纯契约新增)

```markdown
## Slices

### S-001: Session export function 契约

- 完成标志:`auth_export_user_session("u-1")` 返回 `Session(user_id="u-1", token="session-u-1")`,unit test 通过
- 代码锚点:services/auth/exports.py [existing]
- 测试:test_auth_exports.py 覆盖正常 + 边界

### S-002: Public wiring(route + registry)契约

- 完成标志:`/api/auth/session/export` 注册到 `auth_export_user_session` + `EXPORT_REGISTRY["auth.session"] == "auth_export_user_session"`,两条独立 e2e 断言
- 代码锚点:api/auth_routes.py [existing];registry/export_registry.py [existing]
- 测试:test_auth_exports.py 加 registry / route wiring 断言

### S-003: 回归自检

- 完成标志:既有 role export 行为不变(测试通过)+ 新 session export 全套通过
- 测试:运行 test_auth_exports.py 全套
```

每个 slice 都是独立可验证的契约,无需等到末期集成才暴露问题。

### 中需求(功能 + 状态机 + walking skeleton)

```markdown
## Slices

### S-001: Walking skeleton — 课程列表 e2e 通

- 完成标志:`GET /api/courses` 返回种子数据(2 条)+ 首页渲染列表 + e2e 测试通过
- 数据 / schema:courses 表 [new] minimal(id / title / description)
- 代码锚点:Next.js 框架 + DB connection [new];首页 page [new];courses API [new]
- 测试:e2e_courses_list.spec.ts

### S-002: User 注册 + 登录契约

- 完成标志:`POST /api/register` + `POST /api/login` 端到端通,session token 写入,`GET /api/me` 返回 user
- 数据 / schema:users 表 [new]
- 代码锚点:auth service [new];3 个 API [new]

### S-003: Auth middleware + role 鉴权契约

- 完成标志:protected route 无 token → 401;有 token 但 role 不符 → 403;通过 → 200,各场景独立 assertion
- 代码锚点:auth middleware [new];3 个测试用 protected endpoint
- 测试:auth_middleware.test.ts

### S-004: Order pending 创建契约

- 完成标志:登录用户 `POST /api/orders {course_id}` 创建 pending order;同 idempotency_key 重复请求不重复创建
- 数据 / schema:orders 表 [new]
- 代码锚点:OrderService [new];orders API [new]

### S-005: Payment 沙盒回调 → 状态流转

- 完成标志:沙盒成功回调 → order pending → paid;失败回调 → pending → failed;状态机不可逆向
- 代码锚点:PaymentService [new];callback API [new];状态机 [new]
- 测试:payment_state_machine.test.ts

### S-006: Enrollment 在 paid 时自动建立(行为契约)

- 完成标志:order paid 后 enrollments 自动写入 `(user, course)`;`GET /api/me/enrollments` 返回该记录
- 数据 / schema:enrollments 表 [new]
- 代码锚点:EnrollmentService [new];PaymentService 触发逻辑 [extend]
- 测试:e2e order → payment → enrollment 链路
```

S-001 是 walking skeleton(穿透 Next.js + DB + API + UI 栈),后续 slice 站在上面扩展。S-003 是纯技术契约(auth middleware),不是 user feature 但仍是独立可验证小单元(401 / 403 / 200 三种行为各有独立断言)。S-005 / S-006 是状态机 / 行为契约(状态转换、跨服务自动建立),也是独立可验证小单元。

字段由 slice 实际涉及范围决定:S-002 / S-003 没指明 `测试` 字段表示沿用 Testing strategy 默认;S-001 涉及框架 + DB + API + UI 多面所以代码锚点列多项。

## 进度记录

Impl 进度记录在 `task.json.slices` 数组(通过 `sdd-arbor mark-slice` 更新),PRD 里的 Slices 段只定义需求,不做进度标记。
