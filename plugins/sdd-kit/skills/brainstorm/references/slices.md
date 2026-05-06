# Slices

PRD 定稿时必须包含 `## Slices` 段,按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多、切片最精准。

## 写法

每个 slice 用 `### S-NNN: <标题>` 起头,body 用 `- 字段:值` 形式给出。**slice 涉及就写,不涉及就整条省略**,不写 N/A、不留占位。不分存量 / 新项目:是否写某字段只看这个 slice 的实际范围。

### 必填

- `完成标志`:一句话可验证的 done-condition。每个 slice 都写,没有例外。

### 按需

- `数据 / schema`:动到表、数据模型、migration 时写。标注 `[new]` / `[existing]`;项目有 `artifacts/data-model.sql` 时指向具体位置。
- `代码锚点`:动到或新建模块、文件、接口、页面时写。标注 `[new]` / `[existing]`;UI、外部集成、权限变更都归此字段。
- `测试`:Testing strategy 为核心路径 / TDD 时写(覆盖路径 / 边界或 test 文件名);最小验收档可省。

## 完成标志 vs Acceptance Criteria

- **AC**(PRD 顶层 `## Acceptance Criteria`)是**用户视角**的整体验收:"能创建账户并查看月度统计"。
- **完成标志**是每 slice 的**技术视角** done-condition:"账户 API 返回 201,DB 记录已写入"。

定稿时每条 AC 应能追溯到 1 个或多个 slice 的完成标志组合。

## 粒度

由可验证性决定:完成后能用一两句话说清楚"怎么验证"。一个 slice 需要列举 5 个以上独立功能才能描述清楚就太粗,应该拆。slice 数量没有上限。顺序反映依赖:先基建,再核心,再边缘,最后验收。

## 示例

```markdown
## Slices

### S-001: 多租户数据隔离基础

- 完成标志:现有 users / orders / products 表查询自动按 tenant_id 过滤;跨租户查询返回空
- 数据 / schema:tenants 表 [new];users / orders / products 加 tenant_id [existing];migration 20260505_add_tenant_id.sql
- 代码锚点:TenantScope [new] src/scopes/tenant.ts;QueryBuilder 钩子 [existing] src/db/query-builder.ts
- 测试:tenant-scope.test.ts 覆盖 基础隔离 / 跨租户拒绝 / 空租户降级

### S-002: 账户管理页面

- 完成标志:能创建、编辑、删除账户并同步刷新列表
- 代码锚点:src/pages/accounts/* [new];src/api/accounts.ts [existing]
- 测试:accounts-page.test.tsx 覆盖 CRUD 流程 + 空态

### S-003: 项目基建

- 完成标志:`npm run dev` 启动后健康检查 API 返回 200
```

S-001 涉及数据、代码、测试三字段都写;S-002 是纯 UI 没动数据层,所以省 `数据 / schema`;S-003 是基建,只有完成标志。字段由 slice 实际涉及范围决定,不由项目类型决定。

## 进度记录

Impl 进度记录在 `task.json.slices` 数组(通过 `sdd-arbor mark-slice` 更新),PRD 里的 Slices 段只定义需求,不做进度标记。
