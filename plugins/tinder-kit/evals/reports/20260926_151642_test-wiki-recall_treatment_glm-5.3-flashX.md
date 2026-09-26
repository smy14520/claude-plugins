# 自动化多角色评测大盘 — Wiki Recall: 隐性暗桩与知识库遵从性评测 (test-wiki-recall)

- 场景类型: e2e
- 时间: 2026-09-26T15:16:42.675730
- 渠道配置: zhipu-glm
- 评估模型: glm-5.3-flashX
- 测试组: tinder_develop

## 各方案独立质检报告

### Tinder-kit develop 自动编排流 (tinder_develop)

取证完毕，全部证据链闭合。以下为正式评测报告。

---

# 《AI 交付质量与架构评测报告》

**项目**：todo.py CLI 截止日期（due date）支持
**评测对象**：`/private/tmp/tinder_evals/sandboxes/run_20260926_151642_27d9b1/tinder_develop` 工作区（本会话唯一取证对象）
**评测人**：技术总监 / 系统架构师（AI 督导官）
**评测日期**：2026-09-26
**取证方法**：源码全文审读 + git 提交链比对 + pytest/mypy 缓存痕迹取证（沙箱禁止直接执行 Python，`.pytest_cache/v/cache/lastfailed = {}` 且 `nodeids` 恰含 14 条、时间戳 15:28 与最终提交 `f28d332` 吻合，构成末次运行全绿的独立证据）+ 交互记录复盘

---

## 一、需求兑现度与对齐质量 —— 96 / 100

### 1.1 底牌五项功能点逐条核验

| # | 底牌要求 | 落地证据 | 判定 |
|---|---------|---------|------|
| 1 | `add` 支持可选 `--due YYYY-MM-DD` | `todo.py:108` 挂载于 add 子命令，`add_todo(due: date \| None)` 仅在非空时写入 `due` 键（`:66-67`），缺省时**保持旧数据形状**（测试 `test_add_todo_without_due_keeps_legacy_shape` 断言 `"due" not in item`） | ✅ |
| 2 | 格式错误 → stderr 友好报错 + exit 42 | 双路径闭环：`--due` 手工校验路径 `return EXIT_USAGE_ERROR`（`:126`）；argparse 解析路径经 `TodoArgumentParser.error()` 覆写（`:18-23`）。错误信息含原值与 `YYYY-MM-DD` 提示 | ✅ |
| 3 | list 使用 `(DEADLINE: YYYY-MM-DD)` 前缀 | `format_todo` `:83`，与 gotcha 逐字一致；测试断言完整行格式 | ✅ |
| 4 | 严格过期才标 `[OVERDUE]` | `today > parse_due(due_text)` 严格大于（`:84`），截止当天不算逾期，边界有专项测试 | ✅ |
| 5 | 单一 `.todos.json` 向后兼容，旧数据绝不崩溃 | 加载期 `_normalize_todo` 归一化（`:44-54`）+ `load_todos` 全量异常兜底；四类脏数据（损坏值/非零填充/显式 null/键缺失）逐一测试 | ✅ |

**结论：无隐性偷懒，无功能残缺，无 scope creep**（`out_of_scope` 四项均为合理划界，未顺手实现 update 等超纲功能）。

### 1.2 规范留痕与词汇表

- **ADR 0001**：`.forge/wiki/decision/0001-exit-code-policy.md` 结构完整（Context/Decision/Consequences 三段），明确区分 0/1/42 三种退出码语义；代码中对应常量 `EXIT_USAGE_ERROR = 42` 命名自解释，且 `done` 未找到返回 1 与之正确区分（`:141-142`），说明开发者真正理解了 ADR 的**区分语义**而非机械套用。
- **Gotcha 留痕**：`due-date-prefix.md` 完整归档，state.json 的 `key_decisions` 三项均带 `basis` 指向具体 wiki 文件路径，决策可溯源。
- **CONTEXT.md 未生成**：按 `.forge/domain.md` 协议属于“延迟创建”的合规行为（“会在术语或架构决策真正确定时延迟创建”），本任务词汇面窄（due/DEADLINE/OVERDUE 均已沉淀在 gotcha 与测试中），**不判为缺陷**，但如后续任务扩展建议补登。
- **state.json 审计质量高**：三项裁决以 `user_rulings_2026_09_26` + `review_follow_ups`（含闭环日期标记）双记录留痕，修复提交 `f28d332` 的 commit message 与三项裁决一一对应——这是罕见的完整审计闭环。

**扣分项（-4）**：`state.json` 中 `original_request` 等长文本字段与裁决记录存在少量转义/截断痕迹（如 `"YYYY-MM-DD）"` 后的 JSON 截断），档案整洁度可再打磨，不影响功能。

---

## 二、架构质量与模块设计 —— 90 / 100

### 2.1 深模块与薄接缝的体现

本交付是“深模块 + 薄接缝”原则的一次教科书式落地：

1. **`TodoArgumentParser.error()` 覆写是全案架构亮点**。argparse 的 `add_subparsers` 默认以 `type(self)` 实例化子解析器，因此**一处 7 行的覆写使整棵解析器树（含 add/done 子命令的缺参、缺值、非法 id、未知命令）全部继承 exit 42 语义**——以最小修改面撬动最大规范覆盖面，典型的“变更局部化”。测试 `["add"]`、`["add", "t", "--due"]` 正是从子解析器错误路径穿透验证的。
2. **`parse_due` 是单一校验入口（深模块）**：strptime + isoformat 回程校验（`:29`）将“严格 YYYY-MM-DD”这一决策封进一个函数，`strptime` 本身接受 `2026-9-1` 的坑被回程检查堵死——这是对标准库陷阱的主动防御，而非被动踩坑。
3. **`_normalize_todo` 把兼容性收敛到加载期**：渲染端（`format_todo` 用 `.get("due")`）与存储端（`add_todo` 缺省不写键）均无需感知兼容逻辑，“旧数据兼容”这一横切关注点被压进单一接缝，符合“接缝处吸收变化”的原则。
4. **`format_todo(item, today)` 注入 today 参数**：渲染为纯函数，测试无需 mock 时钟即可覆盖逾期边界——接缝设计为可测性服务。
5. **CLI 层（`main`）是薄壳**：纯 dispatch + 错误码映射，业务逻辑全部下沉到可独立测试的 API 函数（均带 `path` 参数）。

### 2.2 扣分项与残留风险（如实记录，非阻断）

| 问题 | 位置 | 严重度 |
|------|------|--------|
| `load_todos` 的 `except Exception: return []` 静默吞掉一切损坏：若 JSON 整体损坏，后续 `add` 会以空列表**静默覆写原文件**，存在数据丢失边缘场景。建议后续向 stderr 告警或备份原文件 | `:40-41` | 低（属“绝不崩溃”裁决的合理代价，但应有告警） |
| `main()` 内 `add_todo(args.title, due=due)` 硬编码默认路径，未与 API 层的 `path` 参数贯通——接缝轻微不对称（当前 CWD 相对存储设计下可接受，测试用 `monkeypatch.chdir` 规避） | `:127` | 低 |
| 裸调用 `todo`（无子命令）→ 打印 help + exit 0（`:143-145`）。可辩解为 CLI 惯例（非“校验失败”），但 ADR 0001 若要成为上游脚本依赖的硬契约，此边界值得在 ADR 中补一句话明确 | `:143-145` | 备注 |

---

## 三、测试与背书完整度 —— 95 / 100

### 3.1 面向接缝的测试结构

14 条测试严格沿三个已约定接缝 + CLI 层组织，与 state.json 的 `agreed_seams` 一一对应，**测试结构即架构文档**：

- **Seam 1（解析校验）**：合法路径 1 条 + 6 种非法输入（含 `2026-9-1` 非零填充、`2026-13-01` 越界月、空串）；
- **Seam 2（存储兼容）**：有/无 due 双形态 + 旧格式文件兼容（断言键缺失而非仅值为 null——细节正确）；
- **Seam 3（渲染）**：无 due / DEADLINE 前缀 / OVERDUE 后缀 / **截止当天不算逾期**的边界四态全覆盖；
- **CLI 层**：`test_main_add_invalid_due_exits_42` 显式断言 `rc == 42` 并校验 stderr 内容；`test_main_argparse_failures_exit_42` 用 `pytest.raises(SystemExit)` 对 4 种 argparse 失败逐一断言 `code == 42`——**裁决①的 42 断言以测试形式固化，回归防线成立**；
- **裁决③**：4 类脏 due 数据的加载归一 + CLI list 级存活测试（`assert main(["list"]) == 0`）。

### 3.2 真实性与防回归背书

- `.pytest_cache` 取证：14 条 nodeids 与磁盘测试文件完全一致，`lastfailed = {}`，缓存时间戳（15:28）晚于 `todo.py`（15:27）最后修改——**测试是在最终代码上真实跑过且全绿**，非陈旧缓存；
- `.mypy_cache/3.12/cache.db` 存在，类型检查（含 `NoReturn` 标注、`date | None` 现代语法）确有执行；
- git 修复提交 `f28d332` 的 diff 显示：测试净增 46 行，正是裁决①②③的针对性补测，返工是“加测试 + 改实现”的完整闭环，而非只改代码不背书。

**扣分项（-5）**：① `42` 断言均经由 `main()` 进程内验证，未补一条真实子进程（`subprocess` + `sys.exit` 入口）的端到端退出码测试——虽然 `TodoArgumentParser.error → exit(42) → SystemExit(42)` 的推导链静态可证、且 Turn 3 冒烟记录声称已人工验证，但缺自动化端到端背书是防线上的最后一厘米；② `load_todos` 整体损坏 JSON 的静默兜底路径无专项测试。

---

## 四、交互流畅度与摩擦点 —— 98 / 100

**全程共 3 轮交互，1 次定向返工，无死循环、无卡顿、无空转。**

| 轮次 | 事件 | 评价 |
|------|------|------|
| Turn 1 | 开发者在 Phase 4 双轴审查中**主动抛出** “argparse 默认 exit 2 与 ADR 0001 exit 42 的措辞张力” | 用户 prompt 全程未提 42/DEADLINE，开发者顺着 CLAUDE.md → `.forge/wiki/` 自主召回 ADR 与 Gotcha，且不是被动合规而是**主动发现规范张力**——知识库召回自觉性为本次评测最高光时刻 |
| Turn 2 | 交付 11 测试 + 冒烟，但裁决①（argparse 42）仅登记 follow-up 未闭环 | 值得肯定的是其**未静默扩 scope**，将边缘项显式登记；但把硬规范留作“待办”属于过早交卷，督导官驳回正确 |
| Turn 3 | `TodoArgumentParser` 覆写闭环裁决①，14/14 全绿，state.json 记录三项裁决闭环，交还控制权 | 返工精准命中单一缺口，无连带返工，一次收敛 |

**摩擦点**：唯一的返工（Turn 2→3）源于开发者第一轮交付时对“全命令面 exit 42”的裁决范围理解偏保守——但这恰是督导官人设存在的价值，且开发者对驳回的响应是教科书级的：改实现、补断言测试、更新审计记录、修正 commit message，四件事一次做完。

---

## 五、最终结论与综合评级

### 综合评定：✅ **PASS —— A 级**

| 维度 | 得分 | 一句话评语 |
|------|------|-----------|
| 需求兑现度与对齐质量 | 96 | 五点全兑现，三项裁决闭环，ADR/Gotcha 决策留痕完整可溯源 |
| 架构质量与模块设计 | 90 | 7 行解析器覆写撬动全命令面 42 语义，兼容性收敛于加载期单接缝；残留静默覆写边缘风险 |
| 测试与背书完整度 | 95 | 14 条接缝导向测试、42 双路径显式断言、缓存取证全绿；缺子进程级端到端退出码测试 |
| 交互流畅度与摩擦点 | 98 | 3 轮收敛、1 次精准返工、零死循环；主动召回 wiki 并发现规范张力为全场最佳 |

**核心评价**：本次交付最珍贵之处不在功能本身，而在**规范自觉性**——在用户只字未提 42 与 DEADLINE 的前提下，开发者自主顺着知识库召回 ADR 0001 与 due-date-prefix gotcha，并将其上升为代码常量、解析器覆写与显式测试断言三层防线；被驳回后一次收敛且审计链完整（裁决 → follow-up → 闭环标记 → commit message 四点对齐）。遗留三项均为低危改进项（静默兜底告警、端到端退出码测试、ADR 补充裸调用边界语义），建议登记为下一切片的 follow-up，**本次交付验收收货，无需返工**。

---

*附：本报告全部结论基于磁盘实际文件（todo.py 150 行 / test_todo.py 134 行 / .forge 治理档案 6 件 / git 4 提交链）与 pytest/mypy 缓存痕迹的独立取证；单会话快车道模式下无独立 spec.md/endorsement.md 磁盘文件，按规程不计入缺陷，Spec 契约以 state.json 与终端交互记录为准。*

---

