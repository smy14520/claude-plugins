# 自动化多角色并发评测大盘 — test-wiki-recall

- 时间: 2026-09-25T21:08:33.402009
- 渠道配置: zhipu-glm
- 评估模型: glm-5.3-flashX
- 评估模式: treatment

## 实验组 (tinder_develop) 评测报告

动态复验通道受限（沙箱禁止执行 Python），已通过三重静态证据链完成核验：种子文件比对、逐条静态追踪、监控记录交叉印证。清理完毕，以下是正式评测报告。

---

# AI 交付质量与架构评测报告

| 项 | 内容 |
|---|---|
| **评测场景** | Wiki Recall Test — Todo CLI 追加截止日期（单切片快车道直通实现） |
| **任务 slug** | `todo-due-date`（state.json: phase=COMPLETED） |
| **评审人** | AI 督导官（技术总监 / 系统架构师） |
| **评审日期** | 2026-09-25 |
| **证据链** | ① 终端交互全记录（4 轮监控笔记）② 交付代码/测试全文 ③ `.forge` 档案（state.json、ADR、Gotcha、2 份 tech-debt 工单）④ 种子文件比对（`scenarios/test-wiki-recall/seed_files/`） |
| **核验方式说明** | 本评审环境禁止执行 Python，动态复跑受限；改用**种子基线比对 + 逐条静态追踪**双重核验，关键行为声明（11 项 pytest 全绿、exit 42、DEADLINE 前缀）与 Turn 4 现场监控记录交叉印证一致。测试快照尾部存在截断（第 10 个测试函数 `test_corrupt_stored_due_degrades_without_crashing` 未完整呈现），以现场运行记录为准。 |

---

## 1. 需求兑现度与对齐质量

### 1.1 底牌条款逐条核验

| # | 底牌硬性条款 | 交付证据 | 判定 |
|---|---|---|---|
| 1 | 存储沿用单一 `.todos.json` | `DEFAULT_FILE = Path(".todos.json")`，`save_todos` 序列化格式与基线逐字一致（`{"todos": [...]}`, indent=2, ensure_ascii=False），无第二存储介质 | ✅ |
| 2 | 旧数据无 `due` 字段安全兼容 | `item.get("due")` 容缺 + 专项测试（`test_format_todo` 第 4 断言、`test_cli_list` 第 3 断言）锁定 legacy 输出**逐字符不变** | ✅（超配：含脏数据降级） |
| 3 | 日期格式 ISO 8601 `YYYY-MM-DD` | `validate_due` = 正则 `^\d{4}-\d{2}-\d{2}$` **+** `date.fromisoformat` 日历校验（拒绝 `2026-02-30`）；7 个非法样本测试覆盖 | ✅ |
| 4 | ADR 0001：非法参数 stderr 友好报错 + **exit 42** | ValueError 路径：`return 42`，stderr 含违规值与期望格式；argparse 缺值路径：`add_parser.error` 覆写路由 42。测试断言 rc==42、err 三要素、stdout 为空 | ✅（`add` 通道全覆盖；`done` 通道缺口见 §1.3） |
| 5 | Gotcha：list 前缀 `(DEADLINE: YYYY-MM-DD)` | `format_todo` 严格实现，且与 Wiki worked example **逐字对齐**（含 `[OVERDUE]` 后缀位置）；专项测试断言 add 确认行**不**带前缀（Gotcha 作用域正确圈定为仅 list） | ✅ |

**结论：5/5 硬条款全部兑现，无隐性偷懒、无功能残缺、无范围蔓延**（state.json 显式圈定 4 项 out_of_scope，未擅自实现排序/逾期通知等镀金功能）。

### 1.2 Wiki Recall 专项评价（本场景核心考点）

这是本评测的真正区分点，开发者表现为“**访谈期强回忆 → 实现期漂移 → 审查期内化**”三段曲线：

- **Turn 1（强）**：Phase 1 访谈中 Q3 即主动援引 exit 42 + stderr，说明开工前已查阅 ADR 0001——非督导提示后被动合规，属主动召回；
- **Turn 2（漂移）**：实现与重构阶段的既有裁决口径滑落为 `(due …)` 前缀与非 0 通用退出码，**Wiki 记忆在编码期间衰减**，需督导按 Persona 协议介入提示才重新锚定。这是本次交付唯一实质规范缺口，且恰是被考察能力的失分点；
- **Turn 3（内化）**：修复不止于督导点名的两条——主动将 argparse 错误路由也纳入 exit 42，援引的正是 ADR 的“**一律**”条款，证明其理解了规范精神而非机械打补丁；
- **Turn 4（对齐）**：输出与 Wiki worked example 逐字一致，并自查出督导未点名的脏 due 降级、零部分写入等衍生场景。

### 1.3 唯一规范缺口：`done` 通道的 argparse exit-2

ADR “所有命令一律 42” 条款下，`done` 子命令传入非整数 ID 仍走 argparse 默认 exit 2。**定性：非隐瞒缺陷，而是经督导裁决（Turn 3）的显式 defer**，已留痕 `tech-debt/issues/01-argparse-exit-2-debt.md`。裁量合理（本切片为 `--due` 交付，改动面克制），但按 ADR 字面仍属未闭合项，计入扣分。

### 1.4 统一词汇表与决策留痕

- **ADR 留痕** ✅：`0001-exit-code-policy.md` 内容与种子逐字一致（核验确认 Wiki 为**预置材料**，开发者是正确引用而非冒认作者，合规）；代码内三处行内注释锚定 ADR-0001，规范可溯源；
- **CONTEXT.md 词汇表** ⚠️ 未生成——按本场景单切片快车道规范属标准行为，**不计缺陷**；统一语言实际由 state.json 的 6 条 seams、模块 docstring（`format_todo` 注明 "per wiki gotcha due-date-prefix"）与 wiki tags.md 承载，补偿充分；
- **spec.md / endorsement.md** 缺席：快车道直通模式，Spec 契约与双轴审查呈现在终端（Turn 2 实际调用了 `tinder-kit:code-review` 技能），合规。

**维度得分：9 / 10**（扣 1 分：Turn 2 实现期 Wiki 漂移 + done 通道 defer 未完全闭合 ADR 字面条款）

---

## 2. 架构质量与模块设计

### 2.1 深模块 / 薄接缝分析

```
validate_due(s) ──── 深度：封装"格式+日历"双重规则与错误消息构造，调用方一行
format_todo(item, today) ─ 深度：封装读侧守卫 + Gotcha 渲染 + OVERDUE 判定三重职责
is_overdue(due, today) ── 纯函数，无副作用，语义单一
main(argv, today=None) ── 薄接缝：时钟注入 → 无需 monkeypatch datetime 即可冻结时间测试
add_todo(..., due=None) ── 写侧不变式：validate 先于任何磁盘写入（零部分写入）
```

- **高内聚**：due 相关逻辑收敛于 4 个函数，无散落；读侧复用 `validate_due` 作为降级守卫，校验规则单一权威源（write 拒绝 / read 降级的语义分叉有注释说明）；
- **低耦合**：`main` 的 list 分支瘦身至 2 行（基线为 3 行打印逻辑）；存储层 `load/save` 与基线零改动，diff 面精准收敛于本次需求；
- **向后兼容即架构**：缺字段、脏字段两条退化路径均有显式设计而非偶然不崩溃。

### 2.2 瑕疵（均已自知并留痕）

1. `add_parser.error = lambda message: (print(...), sys.exit(42))[-1]` —— 对 argparse 实例的运行时覆写是务实 hack，但元组 `[-1]` 惯用法晦涩，宜抽具名函数（工单 02 已覆盖模块拆分诉求）；
2. `--due` 以原始字符串绕开 argparse `type=` 校验是为满足 ADR 的正确妥协，但缺乏 schema 层的统一参数校验入口，多命令扩展时会重演工单 01 的债——开发者已在工单中预判了这一点；
3. 未知子命令 → help + exit 0 沿袭基线，按 ADR 字面可商榷，属基线历史债非本切片责任。

**维度得分：8.5 / 10**（代码量约 +60 行兑现完整需求，密度与边界控制优良；扣分在 argparse 覆写 hack 与校验入口未统一）

---

## 3. 测试与背书完整度

### 3.1 测试矩阵（快照可见 10 个函数，现场记录 11 项全绿）

| 测试 | 保护目标 | 防回归价值 |
|---|---|---|
| `test_basic_crud` | 基线行为不回退 | ✅ 护住存量 |
| `test_add_todo_with_due_stores_iso_date` | due 落盘契约 | ✅ |
| `test_validate_due_accepts/rejects_*` | 严格校验边界（含 `2026-9-1`、`2026-02-30`、`2026/10/01`） | ✅✅ state.json 注明“经变异验证咬合” |
| `test_add_todo_rejects_invalid_due_without_partial_write` | **零部分写入不变式** | ✅✅ 少见的高质量断言（检查文件不存在） |
| `test_format_todo_renders_deadline_and_overdue` | Gotcha 逐字对齐 + 当日不算逾期语义 + legacy 渲染 | ✅✅ |
| `test_cli_add_rejects_invalid_due_with_exit_42` | ADR 三要素（rc/stderr 内容/stdout 干净/无落盘） | ✅✅ 直接背书硬规范 |
| `test_cli_add_confirmation_stays_plain` | Gotcha **作用域负向断言**（add 不加前缀） | ✅✅ 防止过度合规 |
| `test_cli_list_marks_overdue_and_keeps_legacy_output` | 端到端混合数据 | ✅ |
| `test_corrupt_stored_due_degrades_without_crashing` | 脏数据降级 | ✅ 超出底牌要求 |

### 3.2 背书完整度评价

- 测试**面向接缝**而非面向实现：全部经由 `add_todo / format_todo / main(argv, today=)` 公共接缝驱动，`today` 注入使时间相关断言确定性可复现——这是标准的接缝级背书；
- 负向路径覆盖密度高（非法格式、非法日历、缺值、脏存储、无部分写入共 5 类），显著优于同规模交付的平均水位；
- 无独立 `endorsement.md`：快车道规范行为，双轴审查记录在终端（Turn 2 启动 `code-review`，Turn 3 呈现结构化 fixed/defer 裁决清单），**process 背书完整，artifact 背书以 state.json `review_dispositions` 承载**；
- 扣分点：快照截断致第 11 项测试无法在档案中逐字复核；`main` 的 else 分支（help + 0）与 `done` 未知 ID → exit 1 无新增测试（后者为基线既有行为，可接受）。

**维度得分：9 / 10**

---

## 4. 交互流畅度与摩擦点

| 轮次 | 阶段 | 开发者表现 | 督导介入 | 摩擦定性 |
|---|---|---|---|---|
| Turn 1 | Phase 1 访谈 | Q3 给出 (a)/(b) 方案对比并援引 exit 42；Q4 主动圈定排除项 | 拍板方案 + 一次性给出 Gotcha 提示 | ✅ 零摩擦，访谈质量高 |
| Turn 2 | Phase 4 审查 | 8 测试全绿、错误消息已收敛，启动 code-review；但裁决口径漂移为 `(due …)` + 非 0 退出 | **全程唯一纠偏**：重申 ADR 42 + DEADLINE 前缀 | ⚠️ 规范性摩擦 ×1（即 Wiki Recall 考点失分处） |
| Turn 3 | 修复裁决 | 主动路由 argparse 错误至 42；结构化 fixed/defer 清单请求裁决 | 批准 3 修 + defer 2 项另开工单 | ✅ 一次决策即收敛 |
| Turn 4 | 交付验收 | 11 测试全绿、产出 2 份 tech-debt 工单 + 人类把关点移交 | 验收通过，批准 commit | ✅ 收尾干净 |

- **总轮次：4 轮**，全程无死循环、无卡顿、无重复返工；唯一纠偏（Turn 2）在下一轮即闭环，收敛系数 1.0；
- 工程纪律亮点：主动产出 tech-debt 工单并申请人类把关，而非静默吞债或越权扩大切片。

**维度得分：9.5 / 10**（扣 0.5：实现期一次规范漂移本可通过审查清单自查发现）

---

## 5. 最终结论与综合评级

### 评分卡

| 维度 | 得分 | 关键依据 |
|---|---|---|
| 需求兑现度与对齐质量 | 9.0 / 10 | 5/5 硬条款兑现 + 超配（脏数据降级、零部分写入）；扣：Turn 2 Wiki 漂移、done 通道 defer |
| 架构质量与模块设计 | 8.5 / 10 | 深模块薄接缝、diff 精准、不变式显式；扣：argparse 覆写 hack |
| 测试与背书完整度 | 9.0 / 10 | 接缝级测试 + 负向覆盖 + 变异验证 + 作用域负向断言；扣：快照截断、基线分支无新增覆盖 |
| 交互流畅度 | 9.5 / 10 | 4 轮收敛、零死循环、一次纠偏即闭环 |

### 综合评级：**PASS — A**

**评级理由**：交付物完整兑现底牌全部硬性条款且在兼容性、健壮性上主动超配；架构体现深模块与薄接缝的正确直觉；测试具备真实防回归能力并经变异验证。未达 A+/S 的两点保留：① Wiki Recall 本为本场景核心考点，开发者访谈期召回优秀但**实现期发生一次记忆漂移**，依赖督导按 Persona 协议纠偏后才重新锚定——最终交付合规，但自主一致性未满贯；② `done` 通道 exit-2 按 ADR “一律” 字面未闭合，虽以经批准的 tech-debt 工单显式留痕，仍属已登记的规范欠账。

### 后续改进建议（已对应留痕，无需返工）

1. **立即项**：按 `01-argparse-exit-2-debt.md` 将 `error` 覆写提升为共享 error handler，一次闭合全部子命令的 42 语义；
2. **短期项**：按 `02-due-value-type-and-module-split.md` 抽取参数校验 schema 层，避免多命令扩展时重演债；
3. **流程项**：建议在 Phase 4 审查清单中加入“Wiki 硬规范逐条复核”固定步骤（本次 Turn 2 漂移即缺口所在），将督导纠偏前置为自查项。

---

*评审依据与种子比对材料归档于 `plugins/tinder-kit/evals/scenarios/test-wiki-recall/`；本报告基于终端交互记录与交付快照作出，快照尾部截断处已注明并以现场运行记录补证。评审过程中创建的临时校验目录已清理。*

