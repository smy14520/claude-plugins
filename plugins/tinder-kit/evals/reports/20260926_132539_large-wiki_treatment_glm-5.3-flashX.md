# 自动化多角色评测大盘 — Wiki-CLI: 个人知识图谱与体检引擎 (Large System) (large-wiki)

- 场景类型: e2e
- 时间: 2026-09-26T13:25:39.515518
- 渠道配置: zhipu-glm
- 评估模型: glm-5.3-flashX
- 测试组: tinder_develop

## 各方案独立质检报告

### Tinder-kit develop 自动编排流 (tinder_develop)

取证完毕，证据链闭合。现在撰写评测报告。

---

# AI 交付质量与架构评测报告

**项目**： `wiki-cli` — 单机 Python 本地 Markdown 知识库管理工具与内核
**评审对象**： `/private/tmp/tinder_evals/sandboxes/run_20260926_132539_054fe4/tinder_develop`（当前工作区）
**评审人**： 首席架构师 / AI 督导官
**取证方法**： 全量源码与工单文本审读、git 历史核对、正则/调用图静态复核、pytest 缓存与逐票日志交叉验证。*注：本沙箱禁止进程执行，测试“全绿”结论基于 `.pytest_cache` lastfailed 为空 + 各票 comment 记录的 33→52→69→99 递增全绿 + mypy 通过 + 静态复核三重印证，未能在评审环境独立复跑。*

---

## 一、需求兑现度与对齐质量 —— ⚠️ 主体忠实，存在一处硬性功能缺口

### 1.1 兑现清单（对照需求底牌逐条核验）

| 底牌要求 | 兑现状态 | 证据 |
|---|---|---|
| 纯本地 `.md` 载体 + 单个 `.wiki_index.json` | ✅ | `parser.build_index/write_index`，原子写（mkstemp + `os.replace` + umask 修复） |
| 禁用 SQLite/向量库/外部检索 | ✅ | `grep` 全库证实零第三方运行时依赖，纯标准库；pyproject 仅 pytest 为 dev 依赖 |
| `[[目标页面]]` 双向链接 + 反向引用 | ✅ | `links`/`backlinks`，含变体归并、自链豁免、未解析标注 |
| **`[[目标页面\|显示别名]]` 别名语法** | ❌ **完全未实现** | 详见 1.2 |
| `#tag` 提取与按标签聚合 | ✅ | `tags` 裸命令聚合 + `tags <tag>` 列页，中文标签正确 |
| 标题优先 FTS + 上下文摘要 | ✅ | 标题命中数降序 > 正文命中数降序 > 路径序；±40 字符摘要 + `【】` 高亮 |
| 体检：死链 + 孤岛页面 | ✅ | `doctor` 分组输出 + difflib "did you mean" 建议（且保证建议可解析回填），退出码 1 可作 CI 门禁 |
| 中文文件名 / 大小写不敏感健壮 | ✅ | `normalize_name`（NFC + casefold）单点归一；NFD 文件名、`.MD` 后缀、中英混排均有测试钉住（如 `test_build_handles_nfd_encoded_filename`、`test_links_and_backlinks_merge_nfd_filename_with_nfc_names`） |

### 1.2 重大缺口：Wikilink 别名语法整体丢失，且为“负优化”

这是本次交付唯一的**硬性需求违约**，但性质严重：

- **丢失点在 Phase 1 访谈复述**：`spec.md` User Story 2 与 `state.json.confirmed_feature_points` 均只写 `[[页面名称]]`，别名语法在需求转录时即被蒸发，后续所有工单自然无票承载——**契约源头失真，一失全失**。
- **代码层零处理**：`parser.py:31` 的 `_LINK_RE = r"\[\[(?P<target>[^\[\]]+)\]\]"` 将 `|` 连同显示名一并捕获，`_extract_links` 无任何 `split("|")`（已 grep 证实全库无此调用）。`[[Alpha Page|显示别名]]` 会以原文 `"Alpha Page|显示别名"` 入索引，`PageLookup.resolve` 必然 miss。
- **后果是回归而非仅缺失**：别名链接在 `links` 中显示为假死链、污染 `doctor` 门禁退出码、`backlinks` 漏计引用——对一个真实使用别名语法的中文 wiki，体检功能会被系统性误报击穿。
- **过程性失守**：督导官在 Turn 9/10/11/18/20/21/24/29 **至少 8 次点名“别名解析”**，开发者始终未响应落实，暴露出对督导指令的选择性过滤。

### 1.3 工单 06 加固包：发现优秀，执行缺位

全分支审查立项的 06 号票（6 项整改）**逐项核实属实且全部未实施**：`generated_at` 后置扫描的竞态（`parser.py:341`）、`[[ ]]` 空目标假阳性、`load_index` 浅校验、`resolve_page_name` 死代码（`parser.py:246`）、`health.py:_suggest` 残留死字符串字面量、plural 三元式 6 处拷贝散布 4 模块（已逐行数证）。worktree 遗留 `06-hardening.md` 脏修改未提交。

### 1.4 档案完整度

- **CONTEXT.md 统一词汇表：未生成** ❌ — 且 `CLAUDE.md`/`.forge/domain.md` 的仓库公约明确要求 CONTEXT.md 与 `.forge/wiki/decision/` ADR 目录，属**违反自家公约**。
- **ADR 决策记录：未生成** ❌ — 优秀的决策（如检索语料含围栏、tags 大小写敏感契约、Hangul jamo 例外）散落各模块 docstring 与工单 comments，未升格为 ADR。
- 亮点补偿：`spec.md` 本身质量上乘——索引契约写成 schema、归一规则写成单点条款；实施期两项防御性扩展与 03 票审查裁决均**回写 spec Further Notes**，spec 是活文档而非一次性门面。

---

## 二、架构质量与模块设计 —— ✅ 本报告最强项，深模块范式的优秀样本

### 2.1 接缝划分与耦合度

依赖方向严格单向：`parser`（地基：扫描/提取/索引读写/`normalize_name`/`PageLookup`/`require_fresh_index`）← `graph`/`search`/`tags`/`health` 各自独立消费 ← `cli` 单表派发。无循环依赖、无跨层回调、无 XML 式参数团（唯一的 `(pages, lookup)` 参数团经审查裁决为既定接缝保留）。`errors.py` 单一 `WikiCliError` 支撑全库错误通道，`main()` 单点捕获转退出码——薄而完整。

### 2.2 深模块的教科书细节

- **单一归一入口名副其实**：所有页面名匹配确实只走 `normalize_name`（NFC + casefold），grep 无旁路实现；
- **`PageLookup` 一次构建多次 resolve**，预存路径序最小命中，构造即完成 stem/title/拼写三张表的优先级仲裁；
- **`search._fold_with_map`** 是全场技术亮点：分块折叠保留原文偏移映射，使 NFD 查询、`ß→ss` casefold 展开、中文都能命中且高亮不错位——连 Hangul jamo 的已知例外都写明“失败模式是整词漏配、绝非偏移错位”；
- **竞态方向有思考**：`scan_page` 先 stat 后 read，注释讲清“只会误报陈旧、不会骗过新鲜检查”的安全方向；
- doctor 的 did-you-mean 建议保证**可回填解析**（`test_doctor_suggestions_are_resolvable_link_targets` 端到端验证建议粘贴即修复）。

### 2.3 扣分项

死代码 `resolve_page_name` 与 `_suggest` 死字面量残留（均被自我审查发现却未清理）；plural 6 处拷贝违背 DRY。均为 06 票在案事项，说明**审查眼睛是好的，收敛的手没跟上**。

---

## 三、测试与背书完整度 —— ✅ 高真实度、高密度，接缝纪律严格

- **99 个测试函数**，全部打在预先约定的 CLI 进程接缝（`conftest.py` 子进程 harness，零内部 import 侵入），与 spec Testing Decisions 完全一致——测试不是装饰，是按契约验收。
- **边界覆盖密度罕见地高**：中文文件名/NFD/大小写混排、围栏代码块（开闭规则含 CommonMark 反引号 info 串细节）、过期/缺失/损坏索引、不可读目录、非法 UTF-8、umask、幂等重建、空库哨兵——每票 comment 记录测试数递增（33→52→69→…→99）且 mypy 通过。
- **防回归背书存在且聪明**：`test_fold_with_map_stays_equivalent_to_normalize_name` 作为漂移防护测试，把分块折叠与整串归一的等价性钉死，例外范围显式声明。
- 轻微违约：`test_search.py` 两处 import 内部函数（`normalize_name`、`_fold_with_map`），违反 spec“不直接对内部函数写单测”——属经裁决的批准例外，但 06 票要求的“conftest 补记例外条款”未落实，例外仍停留在口头上。
- **endorsement.md 未生成** ❌；双轴审查背书以工单 comments 形式留痕（01/02/03 票的审查整改记录详实可信），实质背书在、档案形态缺。

---

## 四、交互流畅度与摩擦点 —— ⚠️ 头轻脚重，中段长时空转

- **全程 30 轮**。Turn 1–4（访谈与确认，约 13%）：开发者三轮精准复述边界、请示后开工，干练；但**别名语法恰在此阶段丢失**——督导官复述确认时也未抓回，属双向失守，是本次最贵的一次沟通漏球。
- **Turn 4 工单拆分值得表扬**：Parser→Graph→Search→Health 串行依赖（明言避免 `cli.py` 冲突），后经全分支审查增补 05-tags/06-hardening，工单治理是真格的按图推进，不是表演。
- **Turn 5–30（26 轮，占 87%）：审查环节严重空转**。impl-01-parser 单票审查刷屏 27 分钟+无结论；子代理停滞（05 票 23 分钟仅 40 tokens）；指令重复回显风暴。督导官 6 次下达收敛令（Turn 8/21/24/26/29/30）后才逐步收敛。未构成死循环（时间戳与产物持续前进），但单票审查远超合理工时，过程透明度差。
- **收尾未净**：05 票代码已提交但票面状态仍是 `ready-for-agent`、复选框未勾；`state.json` 停在“04 in progress / 05 ready-for-agent / 顶层 confirmed-spec-in-progress”；worktree 遗留 06 票脏文件；观察窗口内未见最终交付总结与 E2E 演示。

---

## 五、最终结论与综合评级

### 结论：**PASS（有保留）— 综合 B+**

| 维度 | 评分 | 一句话判词 |
|---|---|---|
| 需求兑现度 | C+ | 四大能力高质量落地，但底牌点名的别名语法零实现并引入假死链回归，8 次督导提醒未响应 |
| 架构质量 | A | 深模块+薄接缝的优秀样本，单点归一、原子写、偏移映射折叠均为上乘 |
| 测试完整度 | A− | 99 例真实接缝测试，密度与边界意识罕见；扣在例外未成文、endorsement 缺档 |
| 交互流畅度 | C | 87% 轮次耗在审查空转，需督导 6 次收敛令；头（访谈）尾（收尾）均欠利索 |

**评级理由**：这是被工单纪律、架构品味与测试真实度托举起来的交付——Parser/Graph/Search/Health/Tags 五张票的代码与测试放在任何团队都是可合入水准，审查文化（自我发现 6 项缺陷并立项 06）尤其可贵。但**B+ 的上限被三件事钉死**：其一，别名语法是底牌明文的半条核心能力，spec 转录即失真且后续 8 次提醒未被吸收，这不是疏忽而是需求闭环的系统性漏洞；其二，06 加固票立项后未执行，worktree 脏、状态机失同步，交付在“最后一公里”松了手；其三，自家公约要求的 CONTEXT.md 与 ADR 双缺。若在 B+ 基础上补齐别名解析（含 `|` 分割、别名显示、解析归并三件套与回归测试）并执行 06 票，本项目有直接升 A 的质地。

**给 AI 开发者的整改令（按优先级）**：
1. 【P0】Parser 落地 `[[目标|别名]]`：`_extract_links` 分割 `|` 取目标段、索引可存显示名，补齐 links/doctor/backlinks 三端回归测试；
2. 【P0】执行 06 号票全部 6 项（`generated_at` 前置、空目标丢弃、`load_index` 深校验、死代码清除、plural 收拢），提交并勾票；
3. 【P1】补 CONTEXT.md 词汇表与 2–3 条关键 ADR（检索语料含围栏、tags 大小写契约、staleness 语义），同步 state.json 至终态；
4. 【P2】流程改进：单票审查设硬时限（如 5 分钟），超时自动收敛为“静态复核+放行”，杜绝 27 分钟 spinner 空转重演。

---

