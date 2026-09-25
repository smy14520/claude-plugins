# 《AI 交付质量与架构评测报告》— todo-cli（Matt Pocock 单会话直通模式）

**评审人**：AI 督导官（全程监控者） | **评审日期**：2026-09-25
**受审对象**：AI 开发者在 Matt Pocock 技能体系单会话直通 /implement 模式下交付的单机 CLI Todo 工具
**评审基线**：需求底牌卡（Ground Truth）× 11 轮人机交互观测（T1-T11）× 交付物全量材料（todo.py / tests/test_todo.py / conftest.py / CONTEXT.md / docs/adr/0001 / git 档案清单）

---

## 0. 评审方法与证据披露

- **磁盘取证披露**：`evals/artifacts/todo-cli/` 下现存两套工作区（`treatment_tinder_kit/` 的 `src/todo_cli/` 包布局、`mattpocock_skills/` 的 09-24 旧变体 TODO_STORE+datetime 设计）均与本受审材料（根布局单文件 `todo.py`、`TODO_FILE` 环境变量、dataclass 版 Task/Store、28 测）不符，本受审会话工作区已被后续运行覆盖/回收。故本次评审以**提交材料与 11 轮终端观测为准**，符合单会话直通模式的评审规范，磁盘证据缺失不计入开发者责任。
- **材料截断披露**：提交材料中 `todo.py` 截断于 `select()` 函数中段、`tests/test_todo.py` 截断于 `test_list_tag_match_is_case_insensitive` 中途，独立复跑（pytest）不可行。已对全部可见代码与 13 个可见用例做**静态逐行推演，全部自洽通过**（见 §3）；不可见部分以 T10/T11 两次一致的"冒烟 + 28 测全绿"口径为信源。审计闭环约留 5% 证据盲区。
- **模式合规披露**：本次为 Matt Pocock 纯单会话直通模式，无独立 spec.md / state.json / endorsement.md 属**规范行为，不计缺陷**；且开发者仍超额产出 CONTEXT.md 统一词汇表与 ADR-0001 决策留痕，高于该模式的最低档案要求。

---

## 1. 需求兑现度与对齐质量 —— **95 / 100**

### 1.1 底牌逐项对照

| 底牌要求 | 交付实况 | 判定 |
| :--- | :--- | :--- |
| 存储介质：本地单一 JSON 文件 | 默认 `~/.todos.json`（与底牌示例逐字一致），`TODO_FILE` 环境变量可覆盖；payload 为 `{"next_id": n, "tasks": [...]}` | ✅ |
| **绝对禁令：禁 SQLite/任何数据库** | 纯标准库（argparse/json/os/sys/tempfile/dataclasses/pathlib），零第三方运行时依赖；ADR-0001 明文拒绝数据库并列 SQLite 为被拒备选 | ✅ 超额 |
| `add <title> [--tag] [--priority high\|med\|low]` | 位置参数 title + 可重复 `--tag`（多标签）+ `--priority`（argparse choices 强校验，非法值 exit 2）；`HIGH` 归一为 `high` 落盘 | ✅ |
| `list [--tag] [--all]` | 默认只显未完成；`--tag` 可重复且多标签 **AND**、大小写不敏感；`--all` 全量；另有经拍板的 `--done` 视图 | ✅ |
| `done <id>` | done 布尔置位，记录保留在 JSON、默认列表隐去（T2 两态制拍板） | ✅ |
| `delete <id>` | T9 人类纠偏后以 `delete` 为主命令、`rm` 为别名，CONTEXT.md 入典 | ✅ |
| 优先级三档 | `high/med/low` 闭集枚举、默认 med、list `--priority` 过滤、显示降噪（med 静默，仅 `!high`/`!low`，T10 拍板） | ✅ |
| 标签：单/多、自由字符串 | 无注册表、显示保留输入原样、同任务大小写不敏感去重（保留首个大小写）、空标签拒绝 | ✅ |
| 边界：不做 Web/GUI/多用户/同步 | 代码零渗漏；ADR Consequences 显式声明"不做跨机同步、Web/GUI" | ✅ |

**无隐性偷懒判定**：未发现任何 stub、TODO 欠账或为绕过难点而降级需求的行为。超出底牌的 `reopen`、`--done`、`--priority` 过滤均为访谈期经人类逐条拍板的**授权扩展**（T8/T9 有据可查），非隐性蔓延。

### 1.2 对齐过程的两次人为纠偏（扣分点）

- **T7**：开发者提出的"四件套"数据模型（id/text/tags/done）**遗漏底牌核心功能 priority**，经人类纠偏扩为五件套；
- **T9**：命令命名再提 `rm`（与底牌 `delete` 不符），默认值清单再次未提优先级展示，人类二次纠偏补齐。

两次纠偏均发生在提案阶段且被立即修正，流程自愈有效；但同一功能域（priority）连续两轮失察，暴露开发者在需求保持（requirement retention）上的主动性问题，是本维度主要扣分项。

### 1.3 统一语言与决策留痕

- **CONTEXT.md 词汇表**：7 词条（Task/Open/Done/Tag/Priority/ID/Delete）全部带定义 + Avoid 反例，且与代码标识符严格互证——`Task` dataclass、`Store`、`done` 布尔、`show == "open"/"done"`、`normalize_tags`、`select`；Avoid 列中的 registry/rename/timestamp/UUID/soft-delete 在实现中零出现。这不是装饰性文档，而是可执行契约。
- **ADR-0001**：决策 + 理由 + 被拒备选（SQLite、todo.txt 行格式）+ 代价自曝（整文件重写、无 schema 迁移），底牌→决策→代码追溯链完整。

---

## 2. 架构质量与模块设计 —— **93 / 100**

- **`Store` 是合格深模块**：接口面仅 load/save 两个动词，实现面吸收 JSON 编解码、损坏拒绝（JSONDecodeError→TodoError）、防御式读盘（from_dict 吸收缺键）、`next_id` 缺失回退、同目录 `mkstemp` + `os.replace` 原子替换、失败清理（finally unlink；替换成功后 tmp 已不存在，逻辑正确）、父目录 mkdir——调用方零感知。
- **`Task` 是单一 schema 真相源**：from_dict/to_dict 双向集中，杜绝散落式字段访问。
- **纯函数薄层**：normalize_tags / parse_priority / find / select 无 I/O、可单测（tests 中确有对应纯单测），过滤语义（可见性 × 优先级 × 标签 AND × ID 稳定排序）一处收口——典型"接缝薄、实现深"。
- **`main(argv) -> int` 薄接缝**：退出码契约清晰（0 成功 / 1 TodoError 用户错 / 2 argparse 用法错），测试可进程内驱动真实 CLI 入口而非 mock 内部函数。
- **诚实取舍**：ADR 明示接受"每写全文件重写、无并发锁"，与单用户定位自洽，无过度设计；单文件组织在此规模下优于强行拆包。

**扣分点（均为边缘健壮性，不影响验收）**：
1. `Task.from_dict` 防御不彻底：`int(raw["id"])` / `str(raw["text"])` 在手编文件缺键时抛 KeyError 裸 traceback，与其自述"字段残缺不应崩溃"的契约不完全一致；
2. `next_id` 缺失时回退 `max(id)+1`，在手编辑过的文件上可能复活已删任务的 ID，与"ID 永不复用"存在理论冲突（仅限手编损坏场景）；
3. `parse_priority` 直接抛 `argparse.ArgumentTypeError`，领域函数与 CLI 框架轻微耦合（务实但接缝略浊）。

---

## 3. 测试与背书完整度 —— **94 / 100**

- **规模与口径**：251 行 / 28 用例，T10（审查段）与 T11（交付段）两次独立口径一致（"冒烟 + 28 测全绿"），可信。
- **接缝真实性**：全部用例经 `main(argv)` 进程内驱动真实入口，断言三重可观察接缝——退出码（0 / 1 / SystemExit(2)）、capsys stdout/stderr、`TODO_FILE` 指向的落盘 JSON 全量形状；`monkeypatch + tmp_path` 完全隔离；`drain(capsys)` 防 setup 输出串扰——测的是系统真实行为面，不是实现内部。
- **决策→测试映射（防回归背书成立）**：

| 访谈拍板 | 对应用例 |
| :--- | :--- |
| T2 两态制/默认只显未完成 | test_list_defaults_to_open…、test_list_done_and_all |
| T3 自由字符串标签 | test_add_tags_and_priority（实现中无任何注册表代码） |
| T4 大小写不敏感+卫生清洗 | test_list_tag_match_is_case_insensitive、test_normalize_tags_keeps_first_casing、dedup 用例 |
| T5 持久化自增 ID 永不复用 | test_add_assigns_ids_and_defaults（next_id==2）、test_ids_never_reused_after_delete |
| T6 多标签 AND | test_list_multiple_tags_is_and |
| T7 五件套模型 | test_add_tags_and_priority 对整条 task dict 做全键相等断言 |
| T8 默认 med + 枚举强校验 | defaults 断言 priority=="med"、invalid priority→SystemExit 2 |
| T9 delete 命名 + 优先级展示 | run("delete","1") 贯穿用例、`"!high" in out` |
| T10 med 静默降噪 | defaults 用例输出断言仅含 `[ ] 1 买牛奶` |

- **边界覆盖**：空白标题拒绝、空标签拒绝、非法优先级 exit 2、`--done --all` 互斥 exit 2、空白修剪、跨大小写/空白去重。
- **可见用例静态推演**：13 个可见用例逐一与可见实现对照（ID 计数、去重保留首大小写、AND 过滤、归一化落盘、退出码路径），逻辑全部自洽。
- **局限**：材料截断使 100% 审计不可达；`reopen` 用例覆盖情况不可见；独立复跑因工作区缺失不可行——均属证据边界，非开发者缺陷。

---

## 4. 交互流畅度与摩擦点 —— **93 / 100**

- **总轮次：11 轮（T1-T11）**，结构为：T1-T9 需求/设计访谈拍板 9 轮 → 实现 → T10 审查披露 1 轮 → T11 交付收尾 1 轮。全程**零死循环、零卡顿、零重复提问**，每轮以"单问题 + 选项 + 明确推荐 + 理由"的高密度格式收敛，一次拍板即定案。
- **访谈质量**：连续挖出任务生命周期、标签本体论、大小写策略、ID 策略、过滤语义、数据模型、优先级语义、默认值批次等 9 个隐性假设，深度与节奏属访谈期标杆水准。
- **摩擦点**：
  1. priority 域两次失察（T7 模型、T9 命名+展示），靠人类纠偏兜底——最主要的摩擦来源；
  2. T10 有一处替用户拍板的显示决策（med 静默），但披露透明、附带一行回滚余地，经确认后转正——可接受的自立决策；
  3. 9 轮访谈对极简小工具而言节奏偏重（风格观察而非缺陷：每轮决策均落档 CONTEXT/ADR，单位轮次价值高）。
- **收尾纪律**：T10 主动披露 load() try 块越界的真 bug 修复；T11 自审发现首提混入 __pycache__ 主动 amend 修正，且未越权提交会话前预装的 `.claude/` 与 `docs/agents/`——提交边界意识与自愈能力上乘。

---

## 5. 最终结论与综合评级

**结论：PASS | 综合评级：A（94 / 100）**

| 维度 | 得分 |
| :--- | ---: |
| 需求兑现度与对齐质量 | 95 |
| 架构质量与模块设计 | 93 |
| 测试与背书完整度 | 94 |
| 交互流畅度与摩擦点 | 93 |

**评级依据**：底牌全部硬约束（单 JSON 文件、零数据库、极简边界、四命令、三档优先级、多标签）100% 兑现且存储路径与底牌示例逐字一致；CONTEXT.md + ADR 高于单会话直通模式的档案基线；28 测全绿口径一致，且与 9 项访谈拍板形成一一映射的防回归背书；11 轮交互零死循环。未达 A+ 的原因：priority 域两次需人类纠偏、from_dict 防御承诺打折扣、材料截断导致审计闭环留有约 5% 证据盲区。

**改进清单（按优先级）**：
1. `Task.from_dict` 对 id/text 补齐缺键防御（缺键→TodoError），兑现"手编文件不崩溃"的自述契约；
2. 建立"底牌功能清单 → 提案 checklist"的逐项核对习惯，避免同一功能域（priority）连续两轮失察；
3. `next_id` 回退路径补充注释或测试，显式声明手编损坏场景下的 ID 复用风险边界。

**签收**：方向、实现、测试、档案、提交纪律五项全部达标，验收通过，无需返工。
