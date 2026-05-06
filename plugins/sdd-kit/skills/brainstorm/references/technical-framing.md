# Technical Framing

产品 PRD 必须收敛承重技术边界,避免 impl 在关键架构问题上自由发挥。

不要把 Technical Framing 写成实现步骤流水账;只记录会改变 scope、验收或风险的决定。

## Finalize 前至少覆盖

- **Existing stack / framework**:沿用什么、不能引入什么。
- **Auth / permissions**:谁能做什么,权限边界在哪里。
- **Frontend / backend boundary**:页面、API、service、CLI 或脚本边界。
- **Data model / persistence**:新增 / 修改状态、表、缓存、迁移、幂等要求;字段或关系较多时使用 package artifact(如 `artifacts/data-model.sql`)承载草案级 schema contract。
- **Admin / ops surface**:管理后台、配置、观测、回滚入口。
- **External integrations**:第三方、队列、支付、邮件、AI API 等边界。
- **Testing strategy**:用 `AskUserQuestion` 让用户选档位,据此确定覆盖范围和 slice 规划(见下)。
- **Migration / rollout / rollback**:上线、迁移和回退边界;不需要则写 N/A。

## Testing strategy 档位

`AskUserQuestion` 三个选项:

- **核心路径测试**(推荐多数项目):业务逻辑层的关键路径 + 边界 case;外部依赖用 mock / fake。
- **TDD 驱动**(高可靠要求):先写测试再写实现,覆盖所有业务逻辑层;外部依赖用 mock / fake。
- **最小验收**(快速原型):只测 happy path,确认功能跑通。

无论哪档,外部依赖(支付回调、第三方 API)一律通过 mock / fake 隔离,测试的是"收到响应后的业务逻辑",不是真实调用。
