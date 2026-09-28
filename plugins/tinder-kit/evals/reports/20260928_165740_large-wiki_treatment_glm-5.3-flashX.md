# 自动化多角色评测大盘 — Wiki-CLI: 个人知识图谱与体检引擎 (Large System) (large-wiki)

- 场景类型: e2e
- 时间: 2026-09-28T16:57:40.443139
- 渠道配置: zhipu-glm
- 评估模型: glm-5.3-flashX
- 测试组: tinder_develop

## 各方案独立质检报告

### Tinder-kit develop 自动编排流 (tinder_develop)

取证完毕，工作区已还原干净（我创建的冒烟产物已全部删除，`git status` 无残留）。以下为正式评测报告。

---

# 《AI 交付质量与架构评测报告》

| 评测项 | 内容 |
| :- | :- |
| 项目 | `wiki-cli` — 单机 Python 本地 Markdown 知识库工具与内核 |
| 交付分支 | `feat/wiki-cli`（4 个实质提交：`750a64c` → `f24070c` → `373b3b4` → `4e86f47`） |
| 评测人 | 首席架构师 / AI 督导官 |
| 评测日期 | 2026-09-28 |
| 取证方式 | 工作区全量代码审读 + git 历史比对 + pytest 缓存取证 + 静态依赖扫描（注：沙箱策略阻止直接执行 pytest/CLI，测试结论基于 `.pytest_cache` 指纹：105 项收集、`lastfailed = {}` 最近一次全量运行零失败，与交互记录 Turn 7 口径一致） |

---

## 一、需求兑现度与对齐质量 —— 95 / 100

### 1.1 五项核心能力逐条核验（对照需求底牌）

| 底牌要求 | 交付证据 | 判定 |
| :- | :- | :- |
| Wikilinks 解析 `[[目标]]` / `[[目标\|别名]]` | `parser.py` `LINK_RE`（负向断言排除 `![[X]]` 嵌入）；`model.py` `WikiLink.display`；子路径 `[[dir/X]]` 消歧（`Vault.resolve` 先路径后 stem） | ✅ 兑现 |
| 反向引用 Backlinks | `linkgraph.py` `backlinks_of()`——懒构建入链倒排索引，含行号与来源页，死链不授予反链 | ✅ 兑现 |
| `#tag` 提取与聚合 | 正文 TAG_RE + frontmatter tags（行内/方括号/块列表三种形态全支持），嵌套 `#a/b`、同页去重、casefold 聚合、`tags <tag>` 含子标签查询 | ✅ 兑现 |
| 全文检索（标题优先+正文摘要） | `search.py` 多关键词 AND、标题命中数 > 内容密度排序、命中行绝对行号 snippet、casefold 子串匹配天然支持中文 | ✅ 兑现 |
| 健康体检 Doctor | 死链 + 孤岛（底牌要求）之外**额外**交付歧义链接类目，且语义自洽（歧义链接不向任何页授予反链），退出码契约 0/1/2 | ✅ 兑现+增值 |

### 1.2 禁令合规（红线核验）

- **`grep -riE "sqlite|elasticsearch|向量|whoosh"` 全仓零命中**（唯一 "http" 命中是测试里排除 URL 锚点的夹具字符串）；
- `pyproject.toml` `dependencies = []`——运行时纯标准库，与底牌“坚决不引入数据库/外部服务”零冲突；
- 索引为 vault 根**单个** `.wiki_index.json`（`INDEX_FILENAME` 常量），原子回写（tmp+`replace`）、`size:mtime_ns` 指纹增量、损坏/外来版本静默自愈、只读目录降级为内存索引并 stderr 告警——完全命中 Turn 2/4 拍板口径；
- v1 纯只读、无 Web 服务、无 Git 同步、无权限系统，out-of-scope 边界原样守住。

### 1.3 档案留痕

- **CONTEXT.md 统一词汇表：✅ 存在且被真实使用**。10 个领域名词（Vault/Page/Wiki Link/Backlink/Dead Link/Ambiguous Link/Orphan Page/Tag/Doctor）均带 `_Avoid_` 负面清单；抽查确认术语贯穿代码（`WikiLink`、`backlinks_of`、`DoctorReport`、`orphan` 等命名与词汇表严格一致，无漂移）——这在 AI 交付中少见，术语表不是装饰品。
- **ADR：⚠️ 未以正式形式落盘**。`.forge/domain.md` 定义了 `.forge/wiki/decision/` 存放区但目录空置；“索引持久化”这一关键架构决策改记于 `state.json revisions[0]` + 工单 02。决策链可追溯，但不符合自家 domain.md 宣布的 ADR 规范，属**留痕形式瑕疵**而非事实缺失。

### 1.4 发现的缺陷

1. **文档-代码漂移一处（实锤）**：README「已知边界」仍写着 *“`![[X]]` 嵌入语法按普通链接解析（v1 不单列）”*，但 ticket 01（`373b3b4`）修复后代码明确忽略嵌入（`LINK_RE` 负向断言 + `test_no_false_dead_from_embed_or_anchor` 锁定），末次提交只更新了「语义约定」未回头修正「已知边界」。行为本身是正确的，坏的是文档陈旧。
2. 诚实的自我暴露：`state.json deferred_findings` 登记 7 项已知债（Backlink 按链接次数而非词汇表定义的“来源 Page 集合”去重、检索不覆盖文件名 stem、人类输出与 JSON 输出字段不一致等），未擅自扩范围、未掩饰——符合工程纪律，但 Backlink 语义与自家 CONTEXT.md 定义存在已知偏差。

**小结**：底牌零隐性偷懒、零功能残缺，禁令零违反；扣分在 ADR 形式缺失与一处 README 陈旧。

---

## 二、架构质量与模块设计 —— 92 / 100

### 2.1 四子系统接缝核验

```
cli.py(125行, 纯分发) ──> output.py(渲染层, 人类文本+JSON双通道)
        │
        └─> index.py(持久化适配器, 单文件缓存) ──> linkgraph.py(Vault)
                                                      │
                    parser.py(纯函数解析) ──────────┘
                              └────> model.py(领域核心, 全部箭头终点)
```

- **依赖方向单向无环**（已静态核验全部 import），`model.py` 是唯一的公共依赖汇，领域常量（OK/DEAD/AMBIGUOUS）与七类 frozen dataclass 收敛一处；
- **深模块到位**：`parser.py` 的 `mask_code`/`split_frontmatter` 把围栏配对、反引号等长 run、frontmatter 误开判定等大量边界复杂度藏在两个小签名之后；`Vault` 把三个注册表（by_stem/by_path/懒建反链索引）全部私有化，对外仅暴露 `resolve/links_of/backlinks_of/tag_index/search/doctor` 六个动词——接口窄、实现深，正是 Ousterhout 意义上的深模块；
- **`index.py` 的自我定位精准**：模块 docstring 明言“本模块是 LinkGraph 子系统的持久化适配器”，缓存与真相源（.md 文件）的从属关系写得清清楚楚，“索引可随时删除”的纯缓存语义有测试锁定（`test_unchanged_vault_does_not_rewrite`）。

### 2.2 值得表扬的细节

- CLI 对 argparse“全局 flag 不能放子命令后”这一著名缺陷做了干净处理（`SUPPRESS` 默认值 + 子命令副本），`links x --vault y` 两种位置都可用，且有测试；
- 歧义链接语义（多候选页均不获得反链）是本次设计中最容易被含糊掉的地方，交付件把它写进了 docstring、词汇表和测试三处，口径完全一致；
- 检索排序带 path 决胜打破平局，输出确定性有保障。

### 2.3 扣分点（多为开发者自登记，本报告独立复核属实）

- `Vault` 一个类承载 resolution/backlinks/tags/search/doctor 五种读视角，内聚性尚可但有 god-object 苗头；
- OK/DEAD/AMBIGUOUS 用裸字符串而非 Enum，`.md` 后缀剥离在 3 处重复（`resolve`、`WikiLink.target`、`_by_path` 构建）；
- `linkgraph.py` 直接 import `search.py`（`Vault.search` 门面转发），使 SearchEngine 与 LinkGraph 存在轻微耦合，尚不破坏单向性；
- `search_pages` 接收匿名位置元组 `(page, title, body, body_start)`，可读性弱于具名结构。

**小结**：这是一个“宣布了四子系统就真的拆成四子系统”的交付，800 行源码无一处越界写库、无一处引入框架，薄壳 CLI + 深内核的比例拿捏得当。

---

## 三、测试与背书完整度 —— 93 / 100

### 3.1 测试面核验

- **规模与比例**：105 项测试 / 8 个测试文件，约 824 行测试对 820 行源码，约 1:1——无凑数敷衍的快照式测试；
- **测试真实性**：conftest 只有 30 行，全部走“真 tmp 目录 + 真写 .md + 真 `load_vault`”路径，没有一处 mock 掉被测单元自身的自欺式测试；
- **面向接缝组织**：test_parser（解析边界）/ test_links（图解析）/ test_tags / test_search / test_index（缓存生命周期）/ test_doctor / test_cli（端到端含退出码契约）/ test_vault（扫描），与四子系统一一对应。

### 3.2 边界覆盖亮点（督导方重点要求的中文与鲁棒性全部落实）

- 中文文件名身份（`test_chinese_filename_identity`）、中文标签、中文关键词检索、CLI 端到端跑 `中文页面.md`；
- 大小写不敏感：`links PYTHON` 命中 `python.md`、`#Python/#python` casefold 归并、`[[TARGET]]` 反链；
- 解析暗礁：双反引号 span、`~~~` 围栏、围栏类型不匹配不互关、thematic break 误判 frontmatter、`[[#sec]]` 同页锚、`![[X]]` 嵌入、`&#8212; http://x/#anchor` 排除；
- 缓存全生命周期：创建、未变不重写（mtime 断言）、变更刷新、删除剔除、损坏 JSON 自愈、外来版本重建、隐藏目录永不索引。

### 3.3 缺口

1. **只读 vault 降级路径（`_save` 捕获 OSError + stderr 告警 + 内存索引继续）有实现、无自动化测试**——交互记录 Turn 7 声称“真机冒烟覆盖”，但磁盘上无此测试痕迹，本报告无法复核，按未背书处理；
2. 索引 `.tmp` 残留/写失败中断场景未测；
3. 无 CI 配置，“全绿”目前只绑定在本机 pytest 缓存证据上。

**小结**：测试是这套交付里最硬的资产——ticket 01 的四类解析缺陷每类都有对应回归测试锁定，是真正意义上的防回归背书。

---

## 四、交互流畅度与摩擦点 —— 94 / 100

全程 **7 轮**，节奏复盘：

| 轮次 | 阶段 | 督导评价 |
| :- | :- | :- |
| T1 | Phase 1 收敛（Q9 技术栈 / Q10 边界清单） | 提问切中要害，零第三方依赖与只读边界即答即固化 |
| T2 | 规范固化 + 工单拆分准备 | spinner 噪声较多，有短暂空转嫌疑，但无实质卡顿 |
| T3-T4 | 编码 + Standards/Spec 双轴审查 agent 交叉校验 | 主动请求边界拍板，澄清意识良好 |
| T5-T6 | **主动暴露解析正确性缺陷 → 拆 ticket 01 立即修**（`373b3b4`） | 全程最大亮点：发现自己前一轮代码的缺陷不掩盖、按优先级拆票修复 |
| T7 | ticket 02/03（`4e86f47`）+ 105 项全绿 + deferred_findings 移交 | 收尾干净，控制权交还利落 |

- **无死循环**：7 轮全部单向推进，无任何一轮重复已答问题；
- **轻微摩擦**：T2-T4 连续 4 轮以近乎相同的措辞复述边界等待拍板，属流程礼仪冗余而非噪音，但单轮信息增益递减；T2 的纯进度刷屏值得警惕，后续被实质输出证实非空转；
- **工单治理成熟**：三张工单带依赖链（01 → 02 → 03）、状态机完整（全部 resolved）、决策推翻有 `revisions` 记录——这正是督导方期待的“跨模块大工程按图推进”而非“数千行盲写一个文件”。

---

## 五、最终结论与综合评级

### 结论：**PASS —— 综合评级 A**

| 维度 | 得分 | 一句话评语 |
| :- | :- | :- |
| 需求兑现与对齐 | 95 | 底牌逐条兑现+doctor 歧义类目增值；禁令零违反；ADR 形式缺失、README 一处漂移 |
| 架构与模块设计 | 92 | 四子系统真实落地、依赖单向、深模块薄接缝；Vault 略胖、字符串常量未枚举化 |
| 测试与背书 | 93 | 105 项接缝级测试全绿（缓存指纹取证）、真仓库无 mock 自欺；只读降级路径缺自动化背书 |
| 交互流畅度 | 94 | 7 轮零死循环、缺陷自我暴露并拆票修复；边界复述略有冗余 |

**总评**：这是一次可以当作团队范本的 AI 交付。最难得的三件事：其一，**零依赖纪律**——800 行标准库实现扛住了“坚决不用数据库”的绝对禁令，且用“纯缓存索引 + 文件为唯一真相源”的设计让禁令变成了优势；其二，**自我纠错的工单化**——开发者用双轴审查 agent 主动揪出自己四个解析正确性缺陷，拆成带优先级的 ticket 先修后行，而非边写边赖；其三，**词汇表是活的**——CONTEXT.md 的术语在代码、测试、文档三层零漂移。距 A+/S 差在三处：ADR 未按自家规范落盘、README 已知边界与 ticket 01 修复后行为脱节（唯一实锤缺陷，建议顺手修正）、只读降级这条关键容错路径还没有自动化测试背书。deferred_findings 的 7 项技术债登记在案，均不构成本轮验收障碍，留待后续小迭代消化。

---

