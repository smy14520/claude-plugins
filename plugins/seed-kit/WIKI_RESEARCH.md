# seed-kit Wiki 方向研究：项目知识层如何「越用越顺手」

> 一份穷尽式调研的整理。7 路并行检索（WeKnora / docs-as-code / 自更新工具 / 知识图谱 / AI-code-wiki / 失效模式 / agent-memory），65 个一手发现，~97 个来源。目的：为 seed-kit 的 `.wiki/` 找到「随代码活、被流程频繁消费、漂移自愈、越用越准」的形态。
>
> 生成时间：2026-07-01。检索工具：deepwiki / grok-search / exa / WebSearch / WebFetch。

---

## 0. 结论先行（一句话）

**seed-kit 的 wiki 不该是「文档」，而该是「agent 的项目记忆」——一个被开发流程在改 X 前主动召唤、随代码事件增量自愈、锚定稳定单位、且永远清楚自己只是地图不是领土的 compiled 语义层。**

当前 wiki「使用不好」，根因不在工具（`tools/wiki.py` 的 index/search/collect/lint 基础不差），而在它和开发流程的**接缝**：`conventions.md` 明文「五个 skill 互不自动联动，不主动查 wiki」+ hooks.json 三个 hook 没一个碰 wiki → **wiki 是一座孤岛，导航层不被流程消费 = 确定性死层**。

---

## 1. 现状与痛点（代码坐实）

`.wiki/` 是 markdown 导航层（不是 source of truth）：

- **页面模型**：`type`（封闭集：`entity` / `concept` / `gotcha` / `decision` / `source` / `module` / `cross_cut`）× `area`（自由轴，按项目领域）。
- **CLI**：`seed wiki index / search / collect / lint`。
- **链接**：页面间 `[[wikilink]]`，引代码用 `文件:行号` 或符号名。
- **收录**：跨文件链路（「改 X 要动哪几处」）、坑、决策、research 资料。
- **边界**：`module` 类型已有 `source_checkpoint` / `package` frontmatter，lint 已对 module 用行号降级报警。

五个痛点（被多路 research 独立印证，非主观）：

| 痛点 | 表现 | research 印证 |
|---|---|---|
| ① 不自动流转 | impl 不查 wiki、review 不写 wiki、research 不落 | Cline/Roo 把写入钉进 mode 退出动作；codespoon 在 commit 点映射受影响节点 |
| ② 手动 ingest/update 负担重 | 靠用户主动收录/更新 | Ryn Bennett/sync-o：结构性腐烂无法用动机修 |
| ③ 行号漂移 | 代码变 → 行号/页面失效（项目自述「最大失效模式」）| Fiberplane drift / Swimm / codebase-cortex 全部从行号锚迁到符号锚 |
| ④ 导航层死层 | 不被流程消费就是负资产 | Cursor stale-rules 警告；DeepWiki 死层现象 |
| ⑤ lint 能查不能自愈 | 只产 errors/warnings，无修复路径 | living-doc「检测+路由+修复三件套缺一即崩」；WeKnora lint 分级自愈 |

---

## 2. 关键张力（这点决定了所有取舍）

research 多数建议（强制查/强制写/变更触发自动更新）**与 seed-kit 两条铁律冲突**：

- (a) `CLAUDE.md`：「skill 由用户主动触发，不自动流转」
- (b) 栈无关判定式

这不是 research 错，而是 seed-kit 的差异化恰恰在于「AI+人共建、用户主权」。真正的解法：

> **把 wiki 做成「流程节点上零成本可消费的确定性能力」而非「强制流转」**——helper 把 collect / auto-fix / drift-mark 做成一行命令的确定性动作，skill 在天然时机（slice 入口、review 收尾）提议调用，hook 在代码变更点标记待复核，但「是否真的采纳 wiki、是否更新 prose」留给会话与人。**机制确定性，判断留主权。**

这正是 seed-kit 区别于 DeepWiki（全量自动）和企业 KB（人写人读）的位置。

---

## 3. 七路调研发现（每条带来源）

### 路线 A — 腾讯 WeKnora：Compounding Knowledge 范式

WeKnora 是企业级 LLM 知识平台（Go 主导，17K+ stars），源是企业业务文档（PDF/飞书/Notion），**不是代码仓库**。形态不适用 seed-kit，但它的 Wiki Mode（Issue #919）设计思想是本次调研最深刻的发现。

**A1. Compounding Knowledge（越用越顺的总根源）**：把经典 RAG「每次从零重检索」升级为「在原始文档与用户之间维护一个持久、结构化、互链、由 LLM 持续更新的 markdown wiki」。把「综合判断」这个昂贵动作从 query-time 前移到 ingest-time 并持久化；检索质量随沉淀量单调上升。
来源：https://github.com/Tencent/WeKnora/issues/919

**A2. 用户不写 wiki，LLM 全权维护**：用户只策展源、指导分析、问对的问题；LLM 负责全部写作与维护（摘要、交叉引用、归档、簿记）。直接回应痛点①②。
来源：Issue #919, PR #1017

**A3. Slug 连续性规则**：若上一次抽取的实体在当前文档仍存在，复用其精确 slug；不再出现则不纳入；只为真正新实体生成新 slug。→ 同一概念始终指向同一页，**越用越准而非越用越乱**。
来源：DeepWiki 11.7 Wiki Mode；`internal/agent/prompts_wiki.go`

**A4. 漂移自愈分层（WikiLint）**：broken link 自动降级纯文本、stale reference 剥除、empty content 归档（皆 AutoFixable）；orphan page 只警告、missing cross-ref 信息级（不自愈）。`Version` 字段只在用户可见内容真变才递增——区分「机械维护」与「内容过期」。直接打中痛点⑤。
来源：DeepWiki 11.7；`internal/application/service/wiki_lint.go`, `wiki_linkify.go`

**A5. 引用锚到 chunk UUID 而非行号**：`WikiPage.ChunkRefs` 指向源文档稳定切片；wiki 与 raw 冲突时信任 raw 并 flag。→ seed-kit 的 `文件:行号` 漂移对应解：锚稳定切片（符号/commit/AST 节点）。
来源：DeepWiki 11.7（ChunkRefs）

**A6. Wiki Researcher / Wiki Fixer 双 agent + file-back**：Researcher 做 Search-Read-Expand 循环（沿 InLinks/OutLinks 导航，钻 `<sources>` 求真，发现矛盾 flag）；Fixer 读 issue→验证→修复→回填。两个 agent + 一组窄工具构成「查询发现矛盾→flag→fixer 修复→回填」闭环。→ 痛点①④的机制级答案。
来源：DeepWiki 5.3 Agent Mode；`builtin_agents.yaml`

**A7. 查询分类路由**：概念/关系/「怎么做」→ 优先 wiki；精确事实/引文/代码级 → 优先 chunks；混合 → 先 wiki 建概念图再钻 chunks。→ 给 seed-kit「wiki 何时该被消费」的明确判据。
来源：DeepWiki 11.6 Hybrid Retrieval

**不适用（明确避开）**：WeKnora 是重基础设施（Go 服务端 + 多向量库 + Redis + Asynq + MinIO + 多租户 RBAC）；对代码无语义感知（把代码当文本切块+向量化）；源是企业文档非代码。**只借思想，不借形态**。

---

### 路线 B — docs-as-code / living documentation / ADR

**B1. Docs-as-Code**：文档用写代码的工具和流程（Git/Markdown/PR/CI），核心收益是「可以阻塞合并——新功能不带文档不让 merge，倒逼在记忆新鲜时写」。文档与代码同 SHA、同 diff、同 review，天然抗漂移。
来源：https://www.writethedocs.org/guide/docs-as-code/ ；https://technology.blog.gov.uk/2017/08/25/why-we-use-a-docs-as-code-approach-for-technical-documentation/

**B2. Living Documentation（Cucumber/BDD）**：「随代码以同等速率变化的、被验证过的文档」。feature 文件既是测试又是文档，测试跑过即文档有效（green=valid）。文档有了「可执行的真相源」，不依赖人记得更新。
来源：https://medium.com/@lukejpreston/living-documentation-write-better-tests-and-better-docs-147eefe65ab ；https://support.smartbear.com/cucumberstudio/docs/bdd/living-doc.html

**B3. Diátaxis / Divio 四象限**：「文档不是一种东西，是四种」——tutorial（学）/ how-to（做）/ reference（查）/ explanation（懂）。按读者意图切四个正交象限。已被 Django/Cloudflare/Gatsby 采用。
来源：https://diataxis.fr/ ；https://docs.divio.com/documentation-system/

**B4. Architecture Decision Records (ADR)**：短文档捕获单个决策 + 上下文 + 后果 + 置信度。**一旦 accepted 不可改，要改就写新 ADR 并把旧 ADR 标 superseded**。决策是「点时间快照」，记录当时权衡而非当前状态——所以天然不会随代码漂移。
来源：https://martinfowler.com/bliki/ArchitectureDecisionRecord.html ；https://github.com/architecture-decision-record/architecture-decision-record

**B5. 文档漂移检测**：CI 里 lint 死链/行号、AST 语义指纹比对代码与文档、PR-time 把 diff 喂给 LLM 判断哪些页该更新。GetDX 2025：文档不新，新人慢 2-3 个月上手，开发者每周花 3-10 小时找本该已文档化的答案。
来源：https://dosu.dev/blog/how-to-catch-documentation-drift-claude-code-github-actions ；https://www.mintlify.com/library/how-to-stop-documentation-drift

**B6. AI 驱动的文档自愈管线（AutoMem 4 个月生产实践）**：每个源仓 push → git diff 匹配 `file-doc-map.json`（代码文件→文档页映射）→ 命中则 checkout 精确 SHA、跑 Claude Code Action 读改动 + 受影响页 → 开 follow-up PR → auto-merge gate 区分「干净自愈」vs「有歧义等人」。关键：**显式 code→doc 映射（非 AI 猜）+ 确定性更新不用 AI + AI 只做窄任务**。
来源：https://drunk.support/we-wired-three-repos-to-keep-docs-honest-heres-every-file/

---

### 路线 C — 自更新/代码耦合文档工具

**C1. Fiberplane drift（最贴近 seed-kit 当前形态的开源工具）**：markdown 用 `path#Symbol@provenance` 三段式锚点绑代码；tree-sitter 解析 symbol 子树做「归一化 AST 哈希」（XxHash3：node kinds + token text，忽略 whitespace/position）。**reformat / 行号漂移 / 无关改动都不误报，只有 symbol 真改才 stale**。`drift check` 在 CI 阻塞 merge。作者原话点破 seed-kit 痛点：「现有方案都只同步代码 example，不同步描述代码的 prose」「扔 LLM 每次回答 doc 是否 stale 对一个本该 trivial 的检查太贵」。
来源：https://fiberplane.com/blog/drift-documentation-linter/ ；https://github.com/fiberplane/drift

**C2. Swimm Auto-sync（fail-closed 不猜）**：文档 .swm markdown 显式引用代码（smart tokens/smart paths）。代码变时聚合多种加权信号形成直方图决定：自动同步 / 标记需人工重选 / 标记 verified 不打扰。**置信度不足时不猜——留 task 让人 reselect，「we'd rather ask you to reselect than offer a strange suggestion」**。三原则：code-coupled / always-up-to-date / created-when-best。
来源：https://swimm.io/blog/how-does-swimm-s-auto-sync-feature-work

**C3. Strapi Self-Healing Docs（progressive cost gating——最具操作性的范式）**：每周 1:30 AM 扫过去 24h PR，4 级漏斗：Stage0 确定性 shell 正则过滤（chore/test/refactor/Dependabot，砍一半，零 token）→ Stage1 轻量模型只读 title+description 二分 → Stage2 轻量模型读 diff 路由 → Stage3 贵模型才处理结构性改动。2 个月实测 **总 AI 花费 $11.38（约 $0.32/run），107 PR 进 triage，零假阴性**。设计原则：**「Don't use AI for what a regex can do」「下一级永远比漏掉一个 doc gap 便宜」**。
来源：https://strapi.io/blog/building-docs-for-the-ai-era-part-one-self-healing-docs

**C4. mkdocstrings + Griffe**：Python 生态从 source AST 提取 symbol 签名/docstring，build 时渲染。**生成的页不落盘、不进版本控制、每次 build 透明重生成**——API 签名类文档「从 source 生成」是唯一让它物理上无法 stale 的方式。
来源：https://mkdocstrings.github.io/griffe/

**C5. doctest / rustdoc doctests**：文档里的示例变成 assertion，CI 用与代码同等强度验证。drift 表现为 build failure 而非被用户发现。「文档随代码活」的最强形态——但只适用于 example/调用样例。
来源：https://docs.python.org/3/library/doctest.html ；https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html

**根本张力（JSDoc/TypeDoc 揭示）**：prose 越靠近代码越不易 stale 但越难写长叙述；越远离代码越好写但越易漂移。**seed-kit 的 `.wiki/`（独立导航层）正坐在张力易 stale 的一端**——所以更必须用稳定锚 + 漂移自愈来补。
来源：https://tsdoc.org/

---

### 路线 D — 知识图谱 / 双向链接 / typed edges

**D1. 双向链接本质**：普通链接单向，双向链接（1945 Memex → Ted Nelson → Roam/Obsidian/Logseq）让 A 链 B 时 B 自动显示 backlinks。Logseq 用 DataScript 图的 `:block/refs`，backlinks **不是存储而是派生**——零额外写入成本。
来源：https://maggieappleton.com/bidirectionals ；DeepWiki logseq/logseq

**D2. 原子笔记（Zettelkasten）**：每笔记只含一个原子观点，使其可被独立引用、自由重组。Matuschak evergreen notes：笔记应 densely linked，知识 work 应「accrete（累积沉淀）」而非挥发。「越写越顺手」是密度红利：找旧笔记建链 = 自然 spaced repetition。
来源：https://zettelkasten.de/atomicity/guide/ ；https://notes.andymatuschak.org/Evergreen_notes_should_be_densely_linked

**D3. TiddlyWiki transclusion（嵌入引用而非复制）**：引用 tiddler A 时 A 的内容「成为 B 的一部分」——是引用而非拷贝。更新 A，所有 transclude 处自动同步。**复制是腐坏源头；transclusion 通过指向单一源消灭复制，使漂移在结构上不可能**。
来源：https://tiddlywiki.com/static/Transclusion.html

**D4. 代码知识图谱（typed edges）**：代码库 KG（Pharaoh/CodeGraph/Codebase-Memory）用 tree-sitter + LSP 预物化跨文件依赖为可查询图（CALLS/IMPORTS/DEPENDS_ON）。传统探索 = 陌生人逐屋翻找；KG = 预先画好的蓝图，~10x token 节省。
来源：https://pharaoh.so/blog/knowledge-graph-for-code-explained/ ；https://www.harness.io/blog/your-repo-is-a-knowledge-graph-you-just-dont-query-it-yet

**D5. 双向链接批判（DeepRead）**：Obsidian/Roam 的「neutral」等权链接把「组件关系」与「影响关系」混同，连接网变噪音。**链接需要语义类型（typed edges）才有导航价值**。代码 KG 正因 typed edges 才优于 grep。
来源：https://deepread.com/bidirectional-vs-hierarchical-links/

**D6. Living Spec（Wasowski）**：spec drift **只在 silent 时危险**。Ghost document = 写在 Confluence、脱离工程流程、静默偏离。Living spec = 每个 spec-code gap 触发 CI 红线（merge-blocking）。「靠意志力维护所有 spec 必输给 deadline。」
来源：https://levelup.gitconnected.com/living-spec-vs-ghost-document-five-models-that-keep-it-alive-a65b8d304527

**对 seed-kit 的核心借鉴**：
- **backlink 派生而非存储**（lint 扫描 `[[link]]` 与代码引用，派生 backlink map）——让 wiki 主动「找上门」，解决痛点①。
- **typed edges**：链接带语义类型（`touches` 改 X 要动 Y / `depends-on` / `gotcha-at` / `decision-affects` / `refutes`），否则 neutral backlink 堆退化为噪音。
- **transclusion 思想**：引用稳定锚（符号/签名/模块路径），渲染时 helper 实时 resolve 为行号；**行号永不落盘为 wiki 内容**。

---

### 路线 E — AI 时代的代码知识工具

**E1. fiberplane/drift**（同 C1）：AST 符号锚 + `drift.lock` + CI gate。最直接的 seed-kit 升级路径。
来源：https://github.com/fiberplane/drift

**E2. codespoon**：daemon 把 changed files 映射到受影响知识节点，调 agent 改文件，**校验通过则 auto-commit、不通过则回滚**。关键设计：「agent 写文件是契约」——不 parse agent stdout，磁盘文件为准。**「少量精选 curated」而非「全量 ingest」**——和 seed-kit 收录范围高度一致。
来源：https://github.com/rheech22/codespoon

**E3. Devin Knowledge（Notes/Suggestions/Playbooks）——越用越准的 feedback loop**：Notes = trigger 驱动的原子知识；**Suggestions = AI 自动从 chat 反馈/纠错生成「建议新增/更新的 Note」**；人审核接受 → 赋 trigger → 入库。双向：消费侧按 trigger 精准召回，生产侧把每次会话 learnings 自动沉淀成候选。直接命中 seed-kit「越用越准」目标。
来源：https://docs.devin.ai/product-guides/knowledge

**E4. DeepWiki（Cognition）——形态不适用但思想可借鉴**：克隆仓库→AST/依赖 graph→LLM 生成 wiki 页+架构图。**核心矛盾（Latent Space 访谈）：「可编辑」与「随 commit 自动刷新」天然冲突，至今未解**。三个借鉴：①全文 line-level citation 建立信任；②schedule 刷新必然滞后，commit 触发才准；③若 seed-kit 先解「可编辑 vs 自动刷新」就是差异化。
来源：https://cognition.ai/blog/deepwiki

**E5. codebase-cortex——段级 hash + 人编保护 + 验证器**：9 节点流水线，MetaIndex 记录每 section 的 hash 并检测人工编辑（**人编段被保护，不被覆盖**）；独立 DocValidator 节点对照真实代码查事实准确性，低置信标人审；新页打 draft banner 直到 cortex accept。**这是「可编辑 vs 自动刷新」矛盾的工程解——不是二选一，而是段级区分 + 验证门免疫系统**。
来源：https://github.com/sarupurisailalith/codebase-cortex

**E6. Sourcegraph SCIP（精确符号图）**：三档 Precise（SCIP，精确结构感知）> Search-based（文本/正则，近似）> Embeddings（语义向量，非精确）。**「Precise Code Intelligence: An LLM Antihallucinogenogen」**——SCIP 提供 grounded、结构化上下文降低 LLM 幻觉。seed-kit 核心收录（跨文件链路）本质是精确影响面问题，**应偏 precise 符号图而非向量检索**。
来源：https://sourcegraph.com/blog/announcing-scip ；https://www.eric-fritz.com/articles/llm-antihallucinogen

**E7. indxr / nium-wiki / mraza007-codewiki（compiled-not-retrieved 共识）**：一批 Claude Code/Codex skill 工具的共同模式：①**wiki 是预编译语义层，query 取「预消化理解」而非 raw chunk**；②会话/commit 边界触发更新；③增量 = changed-file → 依赖图 → 只重写受影响页（SHA256 幂等）；④**write-back：`wiki_record_failure`（indxr）让未来 agent 不重蹈覆辙**——失败学习闭环；⑤「agent 即智能、CLI 只搬运」验证 seed-kit 分层哲学。
来源：https://github.com/bahdotsh/indxr ；https://github.com/niuma996/nium-wiki ；https://github.com/mraza007/codewiki

---

### 路线 F — 失效模式（要避免什么）

**F1. 「docs lie」共识：stale docs 比 no docs 更坏**。no docs 产生「诚实的未知」；stale docs 产生「自信的错误」。「80% 准确的页面往往比 0% 更坏，因为读者会信任它」。
来源：https://dev.to/tacoda/when-the-docs-lie-27m4 ; https://sync-o.io/blog/stale-documentation-engineering

**F2. 权威文档会关掉 agent 的独立验证本能（2026 预注册基准——对 seed-kit 最致命）**：5 模型、3250 试、$120 自费、open data/harness。给 agent 一段「看起来权威」的文档，它会停止自查——GPT-5.4 被给错文档时任务 100% 做错、验证底层代码率 0%（无文档时验证率 96%）。**stale doc 条件下误导率 68-100%，任务成功坍到 0-32%**。研究者原话：「你的 agent 会相信你递给它的任何文档并停止核查，不管它多聪明，所以这文档最好是对的。」
来源：https://pub.towardsai.net/i-gave-five-ai-models-a-tool-to-fact-check-their-own-documentation-they-refused-to-use-it-bf169988f9d7 ; https://arxiv.org/pdf/2605.06527 （STALE 基准）

**F3. 文档与代码物理分离**：文档过时根因是它「活在代码之外」，更新它需要一次独立动作，而独立动作最容易被跳过。代码有 CI/测试在变东西时 fail；文档没有等价的「可运行校验」。wrong docs 静默失效（invisible problems don't get fixed）。
来源：https://devonair.ai/blog/pain-points/documentation-rot

**F4. GitHub wiki 是 anti-pattern**：不随代码版本化、不在 git clone 里、web 编辑绕过 PR review、fork 不继承 wiki、5000 文件软上限。→ 用 docs/ 目录 + 静态站替代。
来源：https://michaelheap.com/github-wiki-is-an-antipattern/

**F5. 企业 wiki 随规模崩塌的六类结构缺陷（Atlassian 官方）**：space 架构无设计、page 层级混乱、**无 ownership 模型**、命名约定缺失、无轻量治理、搜索优化缺失。典型症状：搜 onboarding 出四个版本；某页 last updated 两年前；同事说「直接问人吧」。
来源：https://community.atlassian.com/forums/App-Central-articles/Why-Most-Enterprise-Knowledge-Bases-Fail-as-They-Scale-And-How/ba-p/3252504

**F6. 腐烂是结构性问题不是写作问题**（Ryn Bennett 600 人公司 4 个月实战）：「文档烂不是人懒，是『保持新鲜不是任何人的工作』，无法用提醒/模板/文化运动修一个结构性问题。你跑活动、做模板、发提醒，6 周后又烂了。」解法不是「让人来找知识」，而是让知识在「工作已经发生的地方」自捕获。
来源：https://medium.com/@ksbennet/your-documentation-doesnt-rot-because-people-are-lazy-403beddca7a6

**F7. context loss 是最隐蔽的腐烂（Scribelet 三速模型）**：reference doc 腐得最快；architecture/decision doc 腐得慢但最灾难（「推理丢了、决策还在生效、没人记得 why」）；最隐蔽的是 **context loss——文档内容没变、周围世界变了，文档读起来仍像对的**。检测它需要「文档为什么这么说」的模型，不只「文档说了什么」。
来源：https://scribelet.app/blog/outdated-documentation

**F8. AGENTS.md/CLAUDE.md 单文件全局化的失败**（Columbia DAPLab 2026）：手动维护、不持续更新、context bloat、缺层级（单根文件让前端 agent 读 DB 索引规则）。OpenAI 建议 agent.md ~100 行。解法是 hierarchical context compressor：按目录自动生成、按 agent 工作目录给精准上下文。→ seed-kit 的 type×area + collect（按 query 取子集）方向优于单文件，但 collect 必须保证「按当前 task 取最小相关子集」。
来源：https://daplab.cs.columbia.edu/general/2026/03/31/your-ai-agent-doesnt-care-about-your-readme.html

**F9. tribal knowledge + bus factor**：「wiki 比工程师活得久」。内部 wiki 多在 18 个月内衰退成噪音。Google 解法：把 markdown 文档放进代码同 repo，融入工程师 workflow。
来源：https://doc.holiday/blog/the-wiki-that-outlives-the-engineer

---

### 路线 G — AI agent 的 memory 机制（最贴近 seed-kit）

**G1. Claude Code memory**：两套互补——CLAUDE.md（人写持久指令）+ auto memory（Claude 自己写的 MEMORY.md，从纠正/偏好学习）。关键：**把这两类知识区分并对应两种写入者**——稳定的「每次都该知道的事实」（人写）vs「从纠正中涌现的模式」（agent 写）。`.claude/rules/` 用 glob 把指令 scope 到特定文件类型/子目录（避免全量加载撑爆 context）。明确警告 <200 行、越具体越可验证越被遵守。
来源：https://code.claude.com/docs/en/memory

**G2. Cline/Roo Code Memory Bank（最贴近 seed-kit 的 agent 维护型 markdown 导航层）**：一组 `memory-bank/*.md`（projectbrief / productContext / activeContext / systemPatterns / techContext / progress / decisionLog），是 agent 跨 session 唯一记忆。核心论点：「我的记忆每次 session 完全重置——这不是限制，正是驱动我维护完美文档的力量。每个 task 开始我 MUST 读全部 memory bank。」**写入触发被编码进 mode rules**：发现新项目模式时 / 实现重大变更后 / 用户说「update memory bank」/ context 需澄清时。不同 mode 负责不同文件。**这是 seed-kit 痛点①（impl 不查/review 不写）的直接对照解**。
来源：https://docs.cline.bot/best-practices/memory-bank ；https://github.com/GreatScottyMac/roo-code-memory-bank

**G3. Cursor rules（description-driven agent 检索）**：规则从单文件 `.cursorrules` 进化到 `.cursor/rules/*.mdc`。Agent Requested 类型——Cursor 只把所有规则的 **description（不是 body）** 作为「菜单」暴露给模型；模型根据当前任务匹配 description，主动 request 对应 rule body。**description = 给 agent 看的检索线索（what/when），body = 给 agent 用的内容**。→ seed-kit：wiki 页 frontmatter 应有 agent 可读的「何时用我」描述，让 impl/review 主动 pull。
来源：https://forum.cursor.com/t/my-take-on-cursor-rules/67535

**G4. Mem0（ADD-only + 多信号检索 + decay）**：写入时 LLM 抽取关键事实，存向量库+实体图，**新事实不覆盖旧事实（ADD-only，保留时序）**。检索融合 semantic + keyword + entity。越用越准：**可选 memory decay——最近被访问的 fact 上浮、陈旧的轻衰减，形成「常用者上浮」强化环**。LOCOMO 上比 OpenAI 高 26%、token 成本省 90%+。
来源：https://arxiv.org/pdf/2504.19413

**G5. Letta / MemGPT（agent 自编辑 memory block）**：core memory（直接注入 prompt）/ archival（语义检索）/ recall。**agent 用一组 memory 工具自编辑**（append/replace/apply_patch/create/delete）。关键洞察：「让 agent 用工具写自己的记忆（不是人写、也不是隐式训练），记忆是 first-class 可读写 artifact。」→ seed-kit：wiki 页面应是 agent 可用 helper 显式 append/replace 的 memory block。
来源：deepwiki letta-ai/letta

**G6. Generative Agents + Reflexion（importance/recency/relevance + 反思升维）**：每条 observation 有 importance（1-10 LLM 打分），检索 score = α·recency + β·importance + γ·relevance；**周期性把低层 observation 综合成高层 reflection，reflection 再插回记忆流且自身可被检索**。Reflexion：跨 episode 维护「自反思文本」作为 verbal reinforcement，失败→写反思→重置→新 trial。→ seed-kit：①反思 = 把零散 gotcha 升维成 decision/pattern；②Reflexion = review 返工时把「为什么返工」固化进 wiki 防再犯。
来源：https://arxiv.org/abs/2304.03442 ；https://promptingguide.ai/techniques/reflexion

**G7. Graphiti（bi-temporal 知识图谱）**：每个 fact 有两条时间线——`valid_time`（现实世界为真的窗口）和 ingestion time（系统何时得知）。**新信息取代旧事实时，旧 fact 被 mark invalid 而非删除，保留完整历史**。→ seed-kit「代码变导致页面过时」的概念级解药：每条代码锚定事实带 valid 窗口，代码 diff 触碰锚点时 fact 被显式 supersede + 重算（保留「曾经为真」痕迹）。
来源：https://github.com/getzep/graphiti ；https://www.getzep.com/blog/temporal-knowledge-graph

**G8. living documentation（staleness 检测 + 路由 + 低摩擦修复三件套）**：「文档死于代码改了却没人检测漂移」。living doc 不是文档类型而是**系统属性**——关键不是「文档怎么生成」而是「系统是否知道自上次准确以来发生了什么变化」。需要三个系统协同：staleness 检测（PR hook 在变更点当场抓）、smart routing（精准发给写代码的人 + 受影响段落）、低摩擦修复（一键审批 <2 分钟）。**三者皆承重，去一即退回静态腐烂**。
来源：https://falconer.com/guides/living-documentation/

---

## 4. 蒸馏的七条核心原则（带依据）

1. **随代码活 = 锚稳定单位而非易变坐标**。行号是易变坐标，符号/commit/内容指纹是稳定单位。drift 用 tree-sitter 对 symbol 子树归一化哈希（忽略 whitespace/position），行号漂移/reformat 不误报；WeKnora 锚 chunk UUID；Swimm 锚 smart token。→ seed-kit 判定式：**每栈给「最稳锚点」（Python 用 ast，其他栈降级为文件内容哈希），对所有栈同等成立**。依据：fiberplane/drift、Swimm、WeKnora ChunkRefs。

2. **被流程消费 = 写入钉进 stage 退出动作，而非靠提醒**。结构性腐烂无法用 prompt 修。Cline/Roo 把 wiki 写入编码进 mode rule 的退出动作；codespoon 在 commit 点由 daemon 映射受影响节点。→ 在 impl/review 的天然时机（slice 收尾、review 通过）消费 wiki，而非另立手动 ingest。依据：Cline memory bank、codespoon、indxr。

3. **漂移自愈 = 检测 + 路由 + 低摩擦修复三件套，分层闸门**。living-doc 论断三件套缺一即崩；Strapi self-healing 4 级漏斗（确定性正则 → 轻量模型 → 贵模型），实测 $11/107 PR、零假阴性；WeKnora lint 分级。**核心铁律：「Don't use AI for what a regex can do」**，把检测/过滤交机器，把判断留人。依据：falconer living-doc、Strapi、WeKnora WikiLint。

4. **越用越准 = feedback→候选→回写 + 高频消费上浮 + 反思升维**。Devin Suggestions 把会话纠错自动提议成候选 Note 经人审；Mem0/Generative Agents 用 similarity+importance+recency 让常用知识上浮；indxr `wiki_record_failure` 把失败结构化回写；Generative Agents reflection 把零散 gotcha 周期性升维成 decision。→ review 的坑/返工原因、impl 确认的决策应被结构化回写，高频被 collect 的页面应自然浮顶。依据：Devin Knowledge、Mem0 arXiv、indxr、Generative Agents。

5. **typed edges：链接必须带语义类型**。DeepRead 批判 Obsidian/Roam 等权链接把「组件关系」与「影响关系」混同；代码 KG 之所以优于 grep，正因用 CALLS/IMPORTS/DEPENDS_ON 区分关系类型。→ seed-kit 已有 type×area 分类页面，但链接本身无类型——「改 X 要动 Y」与「决策约束 Y」应可区分。依据：DeepRead、Pharaoh/Harness code KG。

6. **降级为导航层 + 显式置信度，绝不充当 source of truth**。**2026 预注册基准（5 模型/3250 试）：给 agent 一段看起来权威的文档，它停止自查——stale 条件下误导率 68-100%、验证底层代码率 0%**。权威文档在 context 里「替换」而非「补充」agent 的验证。→ wiki 页面显式标注 last-verified/置信度，agent 拿到 wiki 事实后对易过期项仍必须回查代码。依据：pub.towardsai 5-model 基准、arXiv STALE 2605.06527。

7. **区分知识类型施加不同抗腐策略**。reference 类（易过期、可锚代码）→ 全锚定 + lint；architecture/decision 类（context loss 最隐蔽）→ 带可追踪的前提清单，前提变了触发复核；**ADR 经验：决策是点时间快照，应 supersede 而非原地改**，天然不漂移。依据：Scribelet 三速腐烂模型、Martin Fowler ADR。

---

## 5. 最深洞察：四层 artifact 边界

research 多路收敛，但无人替 seed-kit 画清这层。**这是本次调研最大的贡献**——它界定了 `.wiki/` 该收什么、不该收什么：

| 层 | 角色 | 边界（wiki 不该越界收什么） |
|---|---|---|
| **代码 + PRD** | source of truth（不可变 ground truth） | wiki 永不复制代码事实，只指路 |
| **`.arbor/`** | 任务态（prd.md/slices/checkbox/done-logs，跟任务生灭） | wiki 不收「只在某 task 里有意义」的临时状态（`conventions.md` 已明定「wiki 跟项目走，不跟任务走」） |
| **CLAUDE.md / `.claude/rules/` / DESIGN.md** | 标准层（栈相关、项目定义、harness 自动加载的硬指令） | wiki 不收「对所有会话都该遵守的规则」 |
| **`.wiki/`** | 导航/记忆层 | **只收前三层都覆盖不到的：跨文件链路、坑、为什么这么决定的 rationale、research 资料** |

形态上的三个决定性特征（research 的真正收敛点）：

- **锚稳定单位 + resolve-on-read**：行号永不落盘为 wiki 内容，wiki 存符号/内容指纹，显示时 helper 实时 resolve 成当前行号。漂移从「需修 wiki」降为「resolve 时自动跟代码 / 锚真改时标记」。这根除痛点③，且让 wiki 和代码「物理上无法 disagree」（TiddlyWiki transclusion 思想的代码版）。
- **被流程确定性消费 + 增量事件自愈**：wiki 的活不靠人记，靠 impl/review 的天然时机消费（改 X 前 collect）+ 代码变更事件触发反向定位（改了被引用的代码 → 标记受影响页）。这是「随代码活」的字面实现。
- **降级为参考层 + 显式置信度**：2026 基准证明权威文档会关掉 agent 自查——所以 wiki 必须显式标注 last-verified/置信度，agent 拿到 wiki 事实后对易过期项仍必须回查代码。

---

## 6. 方向建议（6 条，按杠杆排序）

### 建议 1（最高杠杆）：代码引用从「文件:行号」升级为「符号锚 + 内容指纹」，行号 resolve-on-read

页面 frontmatter 声明 `anchors: [hooks/review_gate.py#ReviewGate]`。Python 用标准库 `ast` 解析 symbol 子树、算归一化哈希存为 provenance（或 `.wiki/.anchors.json`）；其它栈无 indexer 时降级为「文件内容哈希」。collect/lint 时 helper 实时把符号 resolve 成当前行号供显示，**行号永不落盘**。lint 比对当前哈希 vs provenance，只对「锚符号真改」报 stale，reformat/行号漂移不误报。

- **why**：痛点③根因是引用粒度太细。drift/Swimm/WeKnora 三路独立收敛到「锚稳定单位」。seed-kit 已有 `source_checkpoint` 先例（module 类），扩展到所有引代码页。判定式成立：每栈给最稳锚点，对所有栈同等成立。
- **tradeoff**：Python 之外无 symbol 级精度（降级文件级哈希，粒度变粗但仍有漂移防护）。不能内置 tree-sitter 全语种（违反「轻量插件」）。

### 建议 2：wiki 读写做成 impl/review 的可选确定性消费点（非自动联动）

消费侧：impl skill 在 slice 入口可选跑 `seed wiki collect --query <slice 主题>` 拉相关 cross_cut/gotcha 注入 context；review skill 在收尾可选把「本轮新坑/被推翻的决策/新跨文件链路」落成候选页。**关键是不违反「用户主动触发」铁律——做成 skill 内的「建议下一步动作 + 一行命令」**，而非 hook 强制注入。配套给页面 frontmatter 加 agent 可读 `description`（学 Cursor Agent Requested rule），让 collect 按「何时用我」精准命中。

- **why**：痛点①④是状态机缺口不是 prompt 问题。Cline/Roo 把写入钉进 mode 退出动作是现成解。
- **tradeoff**：可选消费 ≠ 确定性消费，模型可能跳过。若跳过率高，可后续升级为 review_gate 的软 gate（沿用 v0.3.0 批量证伪 + done 硬 gate 模式）。**先做软、按失败数据再硬化**，符合「不让 workflow 层级膨胀」。

### 建议 3：lint 从「只报漂移」升级为「报漂移 + 分层自愈确定性子集」

借鉴 WeKnora WikiLint 分级 + Strapi 成本闸门。**确定性子集**（broken wikilink / 孤立行号 locator / 空 section）由 lint 直接自动修：broken link 降级纯文本、失效 locator 剥除或标 stale、孤儿页归档移出 collect。**语义子集**（orphan / missing cross-ref / symbol 真改）只标记成 issue 列表交 review。lint 同时输出「当前代码里对应符号的真实签名/值」，让 review 一键采纳而非重新发现（学 Surface C3 条件）。

- **why**：痛点⑤被 living-doc 三件套论断和 WeKnora 分级自愈共同命中。「断链/失效 locator 是确定性的，烧 LLM 太贵」。
- **tradeoff**：自动修有风险（误删有效引用）。必须 **fail-closed**：置信度不足时不猜，抛 review（Swimm 经验：「we'd rather ask you to reselect than offer a strange suggestion」，「can't document a negative」）。

### 建议 4：新增「变更触发」的增量自愈——改了被 wiki 引用的代码 → 反向定位受影响页 → 标记待复核

复用现有 PostToolUse hook 机制（`generate_living_prd.py` 已是 Edit/Bash 触发先例）。新增 wiki drift hook：git diff 触碰某文件，且该文件被某 wiki 页锚定 → 把该页/该锚标 `superseded-需核验`（学 Graphiti bi-temporal：旧 fact invalidate 而非删除，保留「曾经为真」）。**增量而非全量**：按 git diff 变更集只重算受影响页。debounce + 合并多次改动避免噪音（学 WeKnora 30s debounce）。

- **why**：痛点②③。AutoMem/drunk.support 实证的「事件触发 + 显式 code→doc 映射 + AI 窄任务 + auto-merge gate」三件套几乎为 seed-kit 定制。seed-kit 页面已引代码，天然可做 code→page 反向索引。
- **tradeoff**：hook 要快、要确定性（不能每 commit 烧 LLM）。**只做「标记待复核」，不做「自动改 prose」**（后者交给 review 阶段的人/模型）。注意不违反「agent 不自动 commit」——hook 只落标记，不改 wiki 内容、不提交。

### 建议 5：给链接加语义类型（typed edges），并给 decision/gotcha 与 entity/cross_cut 不同生命周期

wikilink 扩展为 `[[页面|rel:类型]]` 或 frontmatter 声明关系：`touches`（改 X 要动 Y）/ `depends-on` / `gotcha-at` / `decision-affects` / `refutes`。collect 按关系类型决定优先级。**decision 类学 ADR**：dated、倾向不可变、变了就 supersede 链接（保留决策史）；entity/cross_cut 类随代码活、需锚定+漂移自愈。给 decision 类加「前提清单」（依赖版本/约束/团队边界等可追踪事实），前提变了触发复核。

- **why**：DeepRead 批判 + 代码 KG 印证——neutral backlink 堆退化为噪音，typed edge 才有导航价值。ADR 印证：决策是点时间快照，原地改丢失「为什么当初这么选」。
- **tradeoff**：typed link 增加 frontmatter 复杂度，与「少即是多」有张力。**可只在 cross_cut/decision 这两类先引入**，不强制全量。

### 建议 6：越用越准的 feedback 闭环——把 review 的坑/返工原因、impl 确认的决策结构化回写为候选页

review skill 收尾时，若判定「这是未来会再踩的坑/新跨文件链路/被推翻的旧决策」，提议一个 wiki 候选条目（draft 状态，带待核验 banner）；impl 确认某设计决策时同理。**候选页过 review 或 lint 验证门后才进 collect 主索引**（学 codebase-cortex DocValidator + draft banner、Devin Suggestions 人审回路）。可选加「最近被 collect 命中次数」信号，让高频页在 search 排序中上浮（学 Mem0 decay、Generative Agents 检索权重）。

- **why**：痛点② + 研究目标「越用越准」。seed-kit 现在没有「把流程 learnings 沉淀回 wiki」的机制——review 发现的坑只活在当次会话，下次重蹈覆辙。
- **tradeoff**：不能让 review 变成「每轮必写 wiki」。做成「可选提议 + draft 验证门」，draft 不直接生效避免 slop。

---

## 7. 反模式（明确要避免）

1. **把 wiki 当 source of truth 给 agent 消费**。2026 基准实证：权威文档关掉 agent 自查本能，stale 时误导率 68-100%。wiki 必须是导航/参考层。
2. **照搬企业通用知识库形态**（WeKnora/Notion/Confluence）：人写人读、靠 curation、和代码无强耦合、重基础设施。只借思想，不借形态。
3. **纯检测不自愈**（只 lint 报漂移、不修）。三件套缺一即崩回静态腐烂。
4. **靠 prompt 反复提醒「记得查 wiki/记得更新 wiki」**。结构性腐烂无法用动机修；应下沉为 skill 退出动作/helper/hook。
5. **每 commit/每 PR 全量 LLM 重写 wiki**。本地插件按 token 成本敏感，会随 commit 线性烧 token 且产 slop。
6. **行号锚定代码**。所有成熟工具已迁符号锚。行号系统性失效——seed-kit 自述「最大失效模式」。
7. **把决策类页面当活页原地改**。ADR：决策是点时间快照，应 supersede 链接，保留「为什么当初这么选」。
8. **让 auto-sync 在语义不明时猜**。Swimm fail-closed 铁律：「宁愿让你 reselect 也不给奇怪建议」。
9. **relink 无脑刷 provenance**。drift relink gate 教训：机制只保证「你被提醒了」，不保证「你真看了」。
10. **把代码/git 当前状态能确认的事实写进 wiki**（与 `CLAUDE.md` 铁律冲突）。wiki 只收不在代码里、易随人流失的 why/坑/链路/决策。
11. **一次性大重构式 wiki 审计替代持续流转**。AutoMem 走过弯路（56 页全量审计），必须靠每次 commit 增量事件触发。
12. **把 wiki 做成 PKM 风格的 graph 可视化**（Obsidian 星座图常被批「看起来复杂但没用」）。图的价值在「可查询的 typed-edge + backlink map」，不在漂亮可视化。
13. **为「像 DeepWiki」做全量一次性外部生成 + schedule 刷新**。必然滞后数小时到数天，且与 seed-kit「项目内、AI+人共建、随 PRD 流程活」冲突——schedule 刷新正是当前痛点①根因。
14. **页面无 owner**（Atlassian 六根因之首、bus factor）。「平台团队拥有 auth 文档」式团队级 ownership 不产出维护；需 named owner + 按变更触发的 review。
15. **纯 neutral 双向链接（无类型）**。DeepRead 证明等权 backlink 堆变噪音。type×area 分类页不够，链接本身必须 typed。

---

## 8. Quick Wins（可马上做的 3 个最小动作）

### QW1【最快见效·根除行号漂移误报】符号锚 + 内容指纹 provenance
给所有引代码页 frontmatter 加 `anchors: [path#Symbol]`，Python 用标准库 `ast` 算 symbol 子树归一化哈希存为 provenance；其它栈降级为文件内容哈希。lint 改为比哈希而非比行号——**立竿见影地让 reformat/行号漂移不再误报，只有 symbol 真改才 stale**。
预期：痛点③的误报噪音归零，lint 信号从「狼来了」变成真信号。纯增量、不破坏现有页面、符合栈无关。

### QW2【打通流程断点·零成本】impl/review 的可选消费点 + description
在 impl SKILL 的 slice 入口加一句「可选：`seed wiki collect --query <slice 主题>` 拉相关 cross_cut/gotcha」，在 review SKILL 收尾加一句「若发现新坑/被推翻决策/新跨文件链路，提议落成 wiki 候选页」。同时在页面 frontmatter 鼓励写 agent 可读的 `description`（何时用我，写场景不写主题）。
预期：痛点①④用最小改动破局——把已存在的 collect 工具接进流程，让导航层第一次被消费。不违反「用户主动触发」铁律。

### QW3【lint 自愈确定性子集·闭合痛点⑤】`seed wiki fix --safe`
在 `wiki_lint` 已有的 errors/warnings 基础上加一个 `seed wiki fix --safe` 子命令，只自动修确定性子集：broken wikilink → 降级纯文本、module 行号 locator 失效 → 剥除或标 stale、孤儿无锚页 → 归档移出 collect。语义类问题（symbol 真改/missing cross-ref）只标记成 issue 交 review。lint 同时输出「当前代码里对应符号的真实签名」供一键采纳。
预期：痛点⑤从「只查不修」变「确定性子集自愈 + 语义子集待人」，且 fail-closed（置信不足不猜）保证不越修越错。

---

## 9. 完整来源索引（~60 条一手资料，去重）

### WeKnora 与企业知识库
- https://github.com/Tencent/WeKnora
- https://github.com/Tencent/WeKnora/issues/919 （Compounding Knowledge 提案）
- https://cloud.tencent.com.cn/developer/article/2651745 （GraphRAG）
- https://community.atlassian.com/forums/App-Central-articles/Why-Most-Enterprise-Knowledge-Bases-Fail-as-They-Scale-And-How/ba-p/3252504

### docs-as-code / living documentation / ADR
- https://www.writethedocs.org/guide/docs-as-code/
- https://technology.blog.gov.uk/2017/08/25/why-we-use-a-docs-as-code-approach-for-technical-documentation/
- https://medium.com/@lukejpreston/living-documentation-write-better-tests-and-better-docs-147eefe65ab
- https://support.smartbear.com/cucumberstudio/docs/bdd/living-doc.html
- https://diataxis.fr/
- https://docs.divio.com/documentation-system/
- https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
- https://github.com/architecture-decision-record/architecture-decision-record
- https://arc42.org/overview
- https://c4model.com/
- https://tom.preston-werner.com/2010/08/23/readme-driven-development
- https://falconer.com/guides/living-documentation/

### 自更新工具 / 漂移检测 / 自愈管线
- https://fiberplane.com/blog/drift-documentation-linter/
- https://github.com/fiberplane/drift
- https://swimm.io/blog/how-does-swimm-s-auto-sync-feature-work
- https://swimm.io/blog/what-is-continuous-documentation-manifesto-part-1/
- https://strapi.io/blog/building-docs-for-the-ai-era-part-one-self-healing-docs
- https://www.mintlify.com/blog/docs-on-autopilot
- https://www.mintlify.com/library/how-to-stop-documentation-drift
- https://drunk.support/we-wired-three-repos-to-keep-docs-honest-heres-every-file/
- https://dosu.dev/blog/how-to-catch-documentation-drift-claude-code-github-actions
- https://mkdocstrings.github.io/griffe/
- https://docs.python.org/3/library/doctest.html
- https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html
- https://tsdoc.org/

### 知识图谱 / 双向链接 / typed edges
- https://maggieappleton.com/bidirectionals
- https://zettelkasten.de/atomicity/guide/
- https://notes.andymatuschak.org/Evergreen_notes_should_be_densely_linked
- https://tiddlywiki.com/static/Transclusion.html
- https://pharaoh.so/blog/knowledge-graph-for-code-explained/
- https://www.harness.io/blog/your-repo-is-a-knowledge-graph-you-just-dont-query-it-yet
- https://deepread.com/bidirectional-vs-hierarchical-links/
- https://levelup.gitconnected.com/living-spec-vs-ghost-document-five-models-that-keep-it-alive-a65b8d304527

### AI 代码 wiki / agent 知识工具
- https://cognition.ai/blog/deepwiki
- https://github.com/sarupurisailalith/codebase-cortex
- https://github.com/rheech22/codespoon
- https://docs.devin.ai/product-guides/knowledge
- https://sourcegraph.com/blog/announcing-scip
- https://www.eric-fritz.com/articles/llm-antihallucinogen
- https://github.com/bahdotsh/indxr
- https://github.com/niuma996/nium-wiki
- https://github.com/mraza007/codewiki
- https://github.com/CodeGraphContext/CodeGraphContext

### 失效模式 / 文档腐坏
- https://dev.to/tacoda/when-the-docs-lie-27m4
- https://devonair.ai/blog/pain-points/documentation-rot
- https://sync-o.io/blog/stale-documentation-engineering
- https://pub.towardsai.net/i-gave-five-ai-models-a-tool-to-fact-check-their-own-documentation-they-refused-to-use-it-bf169988f9d7
- https://arxiv.org/pdf/2605.06527 （STALE 基准）
- https://michaelheap.com/github-wiki-is-an-antipattern/
- https://medium.com/@ksbennet/your-documentation-doesnt-rot-because-people-are-lazy-403beddca7a6
- https://scribelet.app/blog/outdated-documentation
- https://doc.holiday/blog/the-wiki-that-outlives-the-engineer
- https://daplab.cs.columbia.edu/general/2026/03/31/your-ai-agent-doesnt-care-about-your-readme.html

### agent memory / 编码 agent 知识机制
- https://code.claude.com/docs/en/memory
- https://docs.cline.bot/best-practices/memory-bank
- https://github.com/GreatScottyMac/roo-code-memory-bank
- https://forum.cursor.com/t/my-take-on-cursor-rules/67535
- https://arxiv.org/pdf/2504.19413 （Mem0）
- https://langchain-ai.github.io/langmem/concepts/conceptual_guide/
- https://github.com/getzep/graphiti
- https://www.getzep.com/blog/temporal-knowledge-graph
- https://arxiv.org/abs/2304.03442 （Generative Agents）
- https://promptingguide.ai/techniques/reflexion
- https://arxiv.org/html/2504.15228v1 （Self-Improving Coding Agent）
- https://arxiv.org/html/2408.05344v1 （Cody context retrieval）

---

## 10. 给 seed-kit 的总判断

**当前 wiki 的基础（type 封闭集、collect/lint、module source_checkpoint）方向都对，缺的不是重写，是「接缝」**——把 wiki 从孤岛接进开发流程的三个确定性消费点（impl 改 X 前 collect、review 收尾回写候选、代码变更 hook 标记待复核），并把行号锚升级到符号锚（根除漂移误报）、lint 加确定性自愈子集。

执行顺序建议：**QW1（符号锚，根除痛点③误报）→ QW2（流程消费点，破死层）→ QW3（lint 自愈子集）→ 建议 4（变更触发 hook）→ 建议 5/6（typed edges + feedback 闭环）**。前三步是纯增量、不破坏现有页面、不违反两条铁律的最小路径；后三步按失败数据再硬化。

全程守住一个判据：**wiki 是 agent 的项目记忆，不是文档；它随代码呼吸、被流程在改 X 前主动召唤、漂移时自己标记伤口、且永远清楚自己只是地图不是领土。**
