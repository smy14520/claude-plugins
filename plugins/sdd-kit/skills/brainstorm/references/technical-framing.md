# Technical Framing

产品 PRD 必须收敛承重技术边界，避免 impl 在关键架构问题上自由发挥。

不要把 Technical Framing 写成实现步骤流水账；只记录会改变 scope、验收或风险的决定。

## 项目画像

brainstorm 入口推断项目画像（详见 `context-first.md`）。画像决定 Technical Framing 需要覆盖哪些项。

| 画像 | 典型信号 | 关注方向 |
|------|----------|----------|
| **web** | server framework、前端构建、路由文件 | 权限、数据模型、管理面、集成、上线回退 |
| **cli** | manifest `bin` 字段、argparse / clap / cobra | 接口契约、退出码、输出格式、分发 |
| **lib** | 纯导出、无 bin、无 server | API surface、兼容性、错误传播、发布 |
| **data** | pipeline / ETL / 批处理 | 数据流、幂等/重试、观测、schema 演进 |
| **game** | 游戏引擎、game loop、场景文件 | 循环/渲染架构、资产管线、输入、状态/存档、性能预算、平台 |

- 多画像可叠加。
- 不匹配时不要硬套——从项目领域的核心架构关注点自行派生。
- 判断标准：省略该项后 impl 是否会自由发挥导致返工。

## 通用项（所有画像必须覆盖）

- **Existing stack / framework**：沿用什么、不能引入什么。新项目改为 **Tech choices / 技术选型**。
- **Source of truth / 事实源**：当多个层都能表达同一事实时，以谁为准。
- **Implementation Shape / 实现形态**：贴近哪些既有代码形态；功能如何组装；哪些职责不能混在一起。优先参考 repo / framework 已有成功形态。不要写成详细实现步骤或逐文件任务清单。
- **Testing strategy**：用 `AskUserQuestion` 让用户选档位（见下文）。

## 画像特定项

上表的"关注方向"列出了每个画像的典型承重维度。brainstorm 按画像从中选取当前需求真正承重的项写入 PRD，不相关的整条省略。

画像特定项不是固定清单——如果当前需求有上表未列出的承重决策，一样写入 Technical Framing。

## Testing strategy 档位

`AskUserQuestion` 三个选项：

- **核心路径测试**（推荐多数项目）：业务逻辑层的关键路径 + 边界 case；外部依赖用 mock / fake。
- **TDD 驱动**（高可靠要求）：先写测试再写实现，覆盖所有业务逻辑层；外部依赖用 mock / fake。
- **最小验收**（快速原型）：只测 happy path，确认功能跑通。

无论哪档，外部依赖（支付回调、第三方 API）一律通过 mock / fake 隔离，测试的是"收到响应后的业务逻辑"，不是真实调用。
