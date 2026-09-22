# Deepening

在已知 dependencies 的情况下，安全地深化一组 shallow modules。本文件假设你已经使用 [SKILL.md](SKILL.md) 中的核心词汇：**module**、**interface**、**seam**、**adapter**。

## Dependency categories（依赖类别）

评估深化（deepening）候选对象时，先对其 dependencies 进行分类。分类决定了 deepened module 如何跨 seam 进行测试。

### 1. In-process（进程内依赖）
纯计算、内存状态、无 I/O。总是可以深化：直接合并 modules，并通过新的 interface 整体测试。不需要 adapter。

### 2. Local-substitutable（本地可替换依赖）
有成熟本地测试替身的依赖（例如 Postgres 的 PGLite / 嵌入式 SQLite、in-memory filesystem）。如果替身存在，就可以深化。Deepened module 在测试套件中带着替身一起测试。Seam 是 internal 的；module 对外 interface 上不需要预留 port。

### 3. Remote but owned (Ports & Adapters)
由本团队掌控的跨网络服务（微服务、内部专用服务）。在 seam 上定义 **port**（interface）。Deep module 拥有业务逻辑；传输层作为 **adapter** 注入。测试使用 in-memory adapter；生产环境使用 HTTP/gRPC/队列 adapter。

推荐模式：*"在 seam 处定义 port，实现生产的 HTTP adapter 与测试的内存 adapter，使业务核心收拢在单个深模块内，哪怕它跨网络部署。"*

### 4. True external (Mock)
完全无法控制的三方外部服务（Stripe、Twilio、云服务等）。Deepened module 将外部依赖作为注入的 port；测试环境提供 mock adapter。

---

## Seam discipline（接缝纪律）

- **One adapter means a hypothetical seam. Two adapters means a real one.**
  除非至少有两个 adapters 合理并存（通常是 production + test），否则不要过早引入 seam。只有一个 adapter 的 seam 纯粹是无谓的间接层（Indirection）。
- **Internal seams vs external seams**
  深模块内部可以拥有私有 internal seams（供自身集成测试使用），对外拥有 interface 处的 external seam。坚决不要只因为单元测试需要就将内部 seams 泄露到公共 interface。

---

## Testing strategy: replace, don't layer（测试演进：替换而非叠加）

- 一旦 deepened module 的 interface 上建立起了行为测试，旧有的 shallow modules 琐碎单测就变成了维护负担，果断删除它们；
- **Interface is the test surface**：测试通过公共 interface 断言可观测结果，绝不窥探内部状态；
- 测试应能承受内部重构；若实现细节改动迫使测试联动改动，说明测试已经越过 interface 发生了耦合。
