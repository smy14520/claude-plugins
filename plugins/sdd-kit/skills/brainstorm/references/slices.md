# Slices

PRD 定稿时必须包含 `## Slices` 段，按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多、切片最精准。每个 slice 同时生成对应的 `slices/S-NNN.md` task 文件，承载执行细节。

## 切分原则：行为级 checkpoint

每个 slice 是一个**行为级 checkpoint**——对应一个用户可观察行为或系统 invariant，能用一句 Given/When/Then 描述。

可验证的对象可以是：

- **契约**：API / 函数 / 协议的输入输出约定（`POST /api/orders` 创建 pending 订单且 `GET` 返回该订单）
- **功能**：用户 / 调用方可感知的端到端能力（用户能购买课程并立即学习）
- **行为**：不变量、状态转换、对比等价性（支付成功后 enrollment 自动建立）
- **触发链**：状态机 lifecycle 的某次转换或事件回调链（沙盒回调触发 order pending → paid）

### 粒度判定

- **一个主行为**：不要"报名管理模块"；要"参与者成功报名活动"。
- **最多一个主要 mutation / 一个主要查询路径**：页面、action、service、test 可以跨层，但业务目标只有一个。
- **能用一句 When 描述**：如果 When 需要写成"用户做 A 然后做 B 然后做 C"，就太大了。
- **Then 不超过 4-5 条**：如果需要列举 5+ 独立功能才能描述清楚，应该拆。

判定：写完一条"完成标志"后问自己——**"如果只完成这一个 slice 就停下来，系统是否得到了一个可独立验证的新契约 / 功能 / 行为？"** 不能 → 这是 work，合并或重写。

### 反模式：按层切

❌ work-driven（按技术层切，集成债积累）：

```
S-001: 数据 schema 与 migration
S-002: Service 层 CRUD 函数
S-003: API endpoint 注册
S-004: 集成测试
```

S-001 / S-002 / S-003 完成时都"看起来对"，末期 S-004 才发现 schema 缺字段、API 设计不匹配，集成债爆发。

❌ 模块-driven（把多个独立行为塞进一个 slice）：

```
S-005: 主办方可以创建/发布/编辑/取消活动；可以查看报名列表；非 owner 不能操作
```

对人类工程师合理，但对 agent 太厚——里面至少有 5-7 个独立行为，agent 容易做到一半就自认完成。

✅ 按行为级 checkpoint 切：

```
S-001: 创建 todo 后能查询到（最简 schema + 创建 + 查询 + e2e）
S-002: todo 状态可在 open / done 间流转（扩展 schema status + 状态转换 e2e）
S-003: 按状态筛选 todo（查询能力 + e2e）
```

每个 slice 完成时有可独立验证的产物，集成持续偿还。

### Walking skeleton 优先

第一个 slice 通常是 walking skeleton——穿透足够的层让"可验证小单元"立得住：

- 端到端跑通最简 happy path（框架 + DB + auth + 一个 endpoint + e2e test）
- 或最简契约（`POST /api/X` 写入 → `GET` 读取 e2e 通）

后续 slice 站在 skeleton 之上，各自补充某个契约 / 功能 / 行为 / 状态转换。

项目已有领域（课程、订单、用户）→ 第一 slice 用真实领域薄路径（如"课程列表 e2e 通"），**不要默认 `/api/ping` + placeholder page**。仅当项目完全没有任何领域锚点时，才允许用 placeholder endpoint 作为 walking skeleton。

## 护栏：避免退化

### 1. "有测试"不等于独立可验证小单元

单元测试覆盖一个内部函数，但 consumer 还没接上 → 仍是 work，只是披了测试皮。

判断：**下一个 slice 能直接依赖本 slice 产出的契约 / 行为 / 状态吗？** 不能 → 合并或重写。

### 2. API 契约 slice 必须写 consumer 侧验证

"`POST /api/orders` 返回 201" 只是生产侧，不完整。必须有消费侧可观测的验证：

- ✅ `POST /api/orders` 返回 201 + `GET /api/orders/{id}` 返回该订单
- ✅ `POST /api/orders` 返回 201 + 前端订单列表显示该订单

### 3. Walking skeleton 用真实领域最薄路径

见上文 Walking skeleton 段。

### 4. Negative path 必须独立可验证

如果 PRD 写"被阻止 / 拒绝 / 限制"，该 slice 必须有对应的 negative test 或验证。只证 positive action 不算对账通过。当 positive + negative 组合超过粒度标准时，拆成独立 slice。

## PRD 中的写法

每个 slice 用 `### S-NNN: <标题>` 起头。PRD 里只保留**标题 + 完成标志**作为索引；详细的 Acceptance（G/W/T）、Approach、Verification 写在 `slices/S-NNN.md` task 文件中。

### 必填

- `完成标志`：slice 完成后多了什么**可独立验证的契约 / 功能 / 行为**。两种写法：
  - **单行**：slice 只守护一个不变量时用。例：`- 完成标志：调用 X(input) 返回 Y 且测试通过`。
  - **sublist**：slice 里有多个并列 claim 时用（尤其是 **positive action + boundary / negative invariant** 的组合）。每条一个独立可验证 claim。
  - ❌ work："schema 已建"、"function 已实现"、"路由已注册"
  - ✅ 可验证小单元："创建 user-1 后 `GET /users/u1` 返回正确数据"
  - **长句里包含 negative invariant** 时**必须用 sublist 分条**。

### 按需

- `数据 / schema`：动到数据结构、表、文件格式时写。标注 `[new]` / `[existing]`。
- `代码锚点`：动到或新建模块、文件、接口、页面时写。标注 `[new]` / `[existing]`。
- `测试`：Testing strategy 为核心路径 / TDD 时写。

## Slice task 文件

每个 slice 在 brainstorm finalize 前生成对应的 `.arbor/tasks/<package>/slices/S-NNN.md`。这是 impl 的执行指引。

### 结构

```markdown
# S-NNN: <标题>

## Acceptance

Given:
- <前置条件>

When:
- <用户/系统动作>

Then:
- <可观察结果>
- <negative path 结果>

## Approach

1. <推荐实现步骤>
2. ...

## Verification

- <验证命令>
```

### 三段职责

| 段 | 性质 | Agent 必须遵守？ |
|---|---|---|
| **Acceptance** | 硬约束——不满足 = 未完成 | 必须 |
| **Approach** | 推荐路径——可偏离但需满足 Acceptance | 推荐 |
| **Verification** | 确定性验证——命令通过 = done | 必须 |

### Approach 详细度

| Slice 类型 | Approach 详细度 |
|---|---|
| Walking skeleton（穿透多层） | 详细——列出每层要做什么 |
| 纯行为扩展（在已有架构上加功能） | 粗——"参考 S-NNN 的 action 模式" |
| 失败路径 / negative test | 中等——列出要拦截的点 |
| Final gate（纯验证） | 不需要 Approach |

## 完成标志 vs Acceptance Criteria

- **AC**（PRD 顶层 `## Acceptance Criteria`）是**用户视角**的整体验收。
- **完成标志**是每 slice 的**可独立验证产物**。
- **Acceptance**（task 文件的 G/W/T）是完成标志的结构化展开。

定稿时每条 AC 应能追溯到 1 个或多个 slice 的完成标志组合。

## 粒度

由可验证性决定：完成后能用一句 When + 几条 Then 说清楚"怎么验证"。slice 数量没有上限——宁可多而细，不要少而粗。

顺序反映**价值与依赖**：第一个 slice 通常是 walking skeleton；后续 slice 各自补充某个契约 / 功能 / 行为 / 状态转换。**避免按层排列**（先基建 → 再核心 → 再边缘 → 最后验收）。

## 示例

### 中需求（知识付费 — 功能 + 状态机 + walking skeleton）

```markdown
## Slices

### S-001: Walking skeleton — 课程列表 e2e 通

- 完成标志：首页展示 seed 课程（2 条 published），draft 不展示，integration test 通过
- 数据 / schema：courses 表 [new] minimal（id / title / description / price / published）
- 代码锚点：Next.js 框架 + DB connection [new]；首页 page [new]；courses 查询 [new]

### S-002: 用户注册登录

- 完成标志：
  - 注册 → 登录 → /api/me 返回用户
  - 重复邮箱注册返回错误
  - 未登录访问 /api/me 返回 401
- 数据 / schema：users 表 [new]
- 代码锚点：auth service [new]；注册/登录页 [new]

### S-003: 课程详情页

- 完成标志：从列表进入详情，展示完整信息，不存在的课程返回 404 页面
- 代码锚点：课程详情页 [new]

### S-004: 下单 + Stripe Checkout 跳转

- 完成标志：
  - 登录用户点购买 → 创建 pending order → 跳转 Stripe Checkout
  - 同课程重复下单复用已有 pending order
  - 未登录用户被重定向到登录页
- 数据 / schema：orders 表 [new]
- 代码锚点：checkout action [new]；课程详情页购买按钮 [extend]

### S-005: Stripe webhook → 订单状态流转

- 完成标志：
  - checkout.session.completed → order pending → paid
  - 签名验证失败返回 400
  - 重复 event 幂等处理
- 代码锚点：webhook route [new]；order status 更新逻辑 [new]

### S-006: 支付成功自动开通课程

- 完成标志：order paid 后 enrollment 自动创建；/api/me/enrollments 返回该课程；重复不创建
- 数据 / schema：enrollments 表 [new]
- 代码锚点：enrollment 创建逻辑 [new]；enrollments API [new]

### S-007: 学员课程列表 + 学习入口

- 完成标志：登录学员看到已购课程列表，点击进入学习页面，未购买课程不在列表中
- 代码锚点：我的课程页 [new]；学习页 [new]

### S-008: 交付闭环

- 完成标志：npm test 全通过；npm run build 无报错；完整购买链路可走通
```

每个 slice 是一个行为级 checkpoint。S-004 / S-005 各自只管一个状态转换，不把"下单 + 支付 + 开通"塞进一个 slice。

## 进度记录

Impl 进度记录在 `task.json.slices` 数组（通过 `sdd-arbor mark-slice` 更新），PRD 里的 Slices 段只定义需求，不做进度标记。
