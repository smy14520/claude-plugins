# Wiki Tags（受控标签字典）

本项目 Wiki 严格使用以下受控标签。打标必须从本表中选用，严禁在未报备的情况下天天发明新词。
每一个概念只保留一个标准小写英文词，严格禁止使用 `_Avoid_` 中的同义变体。

## 业务领域（Domain）
- `core`: 核心业务逻辑与生命周期
- `auth`: 用户鉴权、Token、Session 与访问控制 (_Avoid_: login, 登录, permission)
- `storage`: 数据存储、持久化、文件读写与序列化 (_Avoid_: store, persistence, 存储, 存盘)
- `cli`: 命令行参数解析、交互界面与退出码规范 (_Avoid_: cmd, command, 终端)

## 技术机制（Mechanism）
- `concurrency`: 进程锁、原子替换、竞态防御 (_Avoid_: lock, 并发)
- `network`: 网络协议、第三方 API 对接与超时重试 (_Avoid_: http, api, web)
- `performance`: 缓存、内存优化与大吞吐处理 (_Avoid_: fast, speed, 性能)
- `error-handling`: 异常分级、Fail-loud 校验与回滚防御 (_Avoid_: exception, 报错, 错误)

---

## 标签扩充规则
1. **优先复用**：既有标签语义能涵盖 70% 时，必须强行复用既有标签；
2. **极严扩充**：只有引入了全项目此前从未涉及的全新独立技术栈或业务子域时，才允许由人类确认在此处追加一行新定义并标明 `_Avoid_`；
3. **单篇数量**：每篇 Wiki 文档的 Frontmatter 标签严格控制在 2~4 个。
