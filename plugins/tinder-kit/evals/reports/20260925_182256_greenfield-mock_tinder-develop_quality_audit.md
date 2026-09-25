# AI 交付质量与架构评测报告 — greenfield-mock × tinder_develop

- 评测对象：sandbox `run-20260925-180113-593ce7/tinder_develop`（单会话 /develop 自动编排流）
- 产物路径：`plugins/tinder-kit/evals/artifacts/greenfield-mock/tinder_develop/`
- 评测人：AI 督导官（技术总监 / 系统架构师）
- 评测方法：需求底牌逐条对照 + 磁盘产物静态复核（源码全文、41 个测试函数逐一核对、git 历史、`.forge` 档案交叉验证）+ 平行流（mattpocock / tinder_manual）横向比对
- 复核声明：审计沙箱内 python 执行需审批未获放行，故未独立重跑 pytest；"41 绿" 以 state.json 声明 + 磁盘 41 个测试函数精确吻合 + 代码路径连贯性做静态采信

---

## 结论速览

| 维度 | 评级 | 一句话结论 |
|---|---|---|
| 1. 需求兑现度与对齐质量 | **B+** | 硬约束全部兑现且留痕，但底牌明文的 `check` 子命令缺失、`serve`/`--config` 命令签名偏离 |
| 2. 架构质量与模块设计 | **A** | 三接缝深模块设计，单一权威实现点，零运行时依赖贯彻彻底 |
| 3. 测试与背书完整度 | **A-** | 41 个面向接缝的真实 socket 测试，含自查 501 漏洞的防回归背书 |
| 4. 交互流畅度与摩擦点 | **B+** | 9 题批量访谈 + 2 个人类闸门，无死循环；但批量"全按推荐"放走了 CLI 偏差 |
| **综合** | **PASS / A-** | 工程品质 A 级，被一条真实的功能缺口（`check` 命令）拉低至 A- |

---

## 一、需求兑现度与对齐质量（B+）

### 1.1 底牌逐条对照

| 底牌条款 | 交付情况 | 证据 | 判定 |
|---|---|---|---|
| 零外部重型框架，纯 `http.server` | ✅ 完全兑现 | 全部 import 为标准库（`http.server`/`json`/`argparse`/`dataclasses`/`threading`/`pathlib`）；`pyproject.toml` `dependencies = []`，仅 dev 组 pytest；ADR-0001 记录 bottle/flask/fastapi 逐一否决理由 | 兑现 |
| 单个 `mocks.json` 静态路由契约 | ✅ 兑现（格式偏差，见 1.2） | `{"routes": [...]}` 数组形态，ADR-0003 论证 | 兑现* |
| `mock-server serve [--config] [--port]` | ⚠️ 部分兑现 | 仅裸调用 `mock-server` 可用；**无 `serve` 子命令**，`--config` 被改名 `--file` | **偏差** |
| `mock-server check [--config]` | ❌ **缺失** | 全仓无 check 入口；`grep -rn "check" src/ README.md` 零命中 | **缺失** |
| 请求捕获与实时日志 | ✅ 兑现 | 每请求一行 stdout：`<ISO时间戳> <client> "<METHOD> <path>" -> <status>`，命中附 ` via <路由指针>`；`test_access_log_*` 正则钉死格式 | 兑现 |
| 未定义路由 404 JSON | ✅ 兑现且超预期 | `test_miss_answers_404_with_json_error_body`；连白名单外 method（PROPFIND）也堵住 stdlib 501 兜底 | 兑现 |
| 配置缺失/格式错误友好退出 | ✅ 兑现 | 缺文件/不可读/校验失败一律退出码 2，全量错误一次性报告（ADR-0002） | 兑现 |
| Out of Scope 三条禁令 | ✅ 零违例 | 无动态脚本、无代理转发、无 TLS；热重载/CORS 也显式排除并写入 spec Out of Scope | 兑现 |
| 项目结构 + CLAUDE.md + 测试 | ✅ 兑现 | src 布局 + console_scripts 入口 + `CLAUDE.md` + 41 测试 | 兑现 |

### 1.2 偏差清单（按严重度）

1. **【主要】`check` 子命令缺失**：底牌 §3 明文要求的核心命令之一，交付中完全不存在。**部分补偿**：fail-fast 装载使 `mock-server --file bad.json` 在绑定端口前完成同等校验并退出码 2（有测试），静态校验能力覆盖约八成；但"校验通过即退出 0、不占端口"的可脚本化语义无法表达，属真实功能残缺。
2. **【次要】`serve` 子命令与 `--config` 旗标未兑现**：能力等价（裸命令即 serve），纯命令面偏差；对按底牌文档敲命令的用户是破坏性差异。
3. **【可辩护】契约格式**：底牌示例为 `"GET /api/user"` 键映射，交付为 routes 数组。底牌用"如"字举例非硬性规定；ADR-0003 给出完整论证（多方法同路径、未来扩展维度不破坏格式），并将映射形态列为 Considered Options 正式否决。平行流中人类亦明示"具体 schema 你定"——**判定为合规的文档化偏差**，但意味着照抄底牌示例的契约文件会报 `must contain a "routes" array`。

### 1.3 对齐质量亮点

- **决策留痕完整且被真实使用**：4 条 ADR 均含 Considered Options / Consequences / Revisit When，且术语（契约/路由/命中/未命中）确实回流进代码 docstring 与测试注释（如 `_respond_miss` 对应 ADR-0004）——不是装点门面的死文档；
- **CONTEXT.md 统一词汇表 8 词条全带 `_Avoid_` 负面清单**，`wiki/tags.md` 受控标签词典 + 打标铁律齐备，词汇纪律可审计；
- **state.json 双人类闸门**（align_confirm / review_commit）留痕，审查记录诚实记录了自查项：2 硬性词汇违规 + 7 smells 修复、3 项超纲严格性上报待裁。

---

## 二、架构质量与模块设计（A）

**三接缝分层，方向干净无环**：`cli`（装配/退出码）→ `contract`（纯数据 + 加载/校验/匹配，零 HTTP 依赖）→ `server`（协议落地，仅消费 `Contract`/`Route`）。CLI 薄（55 行，只做参数→装载→服务），核心厚实。

深模块与单一权威点的教科书式体现：

| 设计点 | 价值 |
|---|---|
| `strip_query()` 全仓唯一命中权威实现 | 匹配语义与 404 回显共用一处，杜绝两处口径漂移（审查记录证实这是审查阶段主动收敛的） |
| `_Handler.__getattr__` 动态分发 `do_*` | 约 6 行同时消灭方法枚举样板 **并堵死 stdlib 501 兜底漏洞**——最小代码量承载最大语义正确性 |
| `_drain_request_body()` | 自觉承担选 stdlib 的协议代价（keep-alive 连接体残留），并用真实同连接双请求测试背书 |
| `log: callable(str)` sink 注入 | 访问日志可被测试捕获断言，stdout 仅是默认实现——接缝即测试点 |
| `port=0` + `address` property | 临时端口消除测试端口竞争，CLI banner 显示内核分配的真实地址 |

内聚耦合俱佳：校验错误全量收集（fail-fast O(1) 排错）、frozen dataclass 不可变契约、`ThreadingHTTPServer` + daemon 线程。挑刺级瑕疵：banner `"1 routes"` 未做单复数、日志时间戳无时区、review 记录提到 ruff 通过但仓库未落 ruff 配置——均不扣架构分。

---

## 三、测试与背书完整度（A-）

- **41 个测试精确吻合声明**（contract 22 / server 14 / cli 5），无注水；
- **测试打在接缝上而非实现细节**：契约测试走真实 `load_contract` 文件路径；服务测试通过 conftest 夹具（写临时契约→真实装载→临时端口后台起服）打**真实 socket**；CLI 测试以 monkeypatch `serve` 接缝捕获装配结果，不启真服务；
- **协议正确性是显式测试义务**（ADR-0001 代价清单逐条有测试）：HEAD 有 Content-Length 无体、keep-alive 同连接连发、PROPFIND 404 JSON、非 ASCII UTF-8、自定义头覆盖 Content-Type、空体无 Content-Type 但有 Content-Length: 0；
- **防回归背书成色最足的一处**：state.json 审查记录明确"1 真问题（白名单外 method 回 501）已修复并加测试"——`test_method_outside_whitelist_still_answers_404_json` 用裸 `http.client` 钉死，这是自查→修复→背书的完整闭环，而非事后补测试；
- **校验面全覆盖**：JSON 语法、根类型、routes 键、路由类型、path 形状、method 白名单、status 200..599（含 `True` 冒充 int 的 bool 陷阱）、body 类型、headers 类型、重复 method+path 拒绝；
- 扣分项：无独立重跑验证（审计环境限制）；`pip install -e .` 后 console_scripts 入口可用这一验收项无法在本审计中复验（静态看 `[project.scripts]` 配置正确）。

---

## 四、交互流畅度与摩擦点（B+）

**轮次重构**（注：tinder_develop 本流的逐轮考评笔记因评测基建故障未落盘——triple 大盘中本流板块为 "Execution error"，另两流为 `OSError: Argument list too long`；以下由 state.json 闸门、spec.md 来源标注与平行流横向比对重构）：

1. **访谈 1 轮**：`/develop` grilling 9 题批量呈现，人类单次"全按推荐、直接开工"（gate_1）——9 个架构分叉（无状态、契约 schema、精确匹配四规则、CORS、404 语义、热重载、绑定/横幅/fail-fast、日志形态、工具链）一轮收口；
2. **单会话实现**：骨架→契约→服务/CLI→测试→冒烟，含内部双轴审查自循环（自查出 501 真问题并修复），**未再打扰人类**；
3. **交付闸门 1 轮**（gate_2）：pytest 41 绿 + 冒烟 + git 提交收束。

全程人类触点约 **2~3 轮**，无死循环、无空转、无返工性卡顿；`MEMORY.md` 中"子代理超时即自查补全"的记忆沉淀亦与单会话不打断的行为自洽。

**摩擦点两处**：
1. **批量"全按推荐"的放行风险成为现实**：底牌明文的 serve/check 子命令在 9 题中从未被摆上桌面，人类批准确认的是一份**已经偏离底牌的 CLI 草案**。对照平行流 mattpocock（13 轮），人类在 Turn 11 主动纠偏"必须保留 serve 与 check"后同样实现了——证明这不是能力边界而是**访谈覆盖缺口 + 橡皮图章确认的叠加**。给批量确认模式敲了警钟：分叉清单再全，也需对照原始需求底牌做一次"承诺 vs 底牌"的最终 diff。
2. **评测基建丢证**：本流交互 transcript 未被捕获（Execution error），使"轮次/卡顿"只能档案重构——属 harness 缺陷而非开发者缺陷，建议修复 argv 超长问题（`Argument list too long`）。

---

## 五、最终结论与综合评级

### 结论：**PASS — 综合评级 A-**

**判定逻辑**：九项硬约束/功能行为全部兑现且有测试与决策留痕，架构与测试品质在同批评测中属第一梯队（501 漏洞自查自修 + 防回归背书是本批唯一）；但底牌明文的 `check` 核心命令实际缺失、`serve`/`--config` 命令签名偏离——能力覆盖约九成、命令面保真约七成。工程深度不足以掩盖一条明文需求的缺席，故从 A 下调至 A-；远高于 FAIL 线，因缺口有部分补偿、偏差有文档、其余全部超额兑现。

**修复建议（预计 <0.5 天）**：
1. `argparse.add_subparsers` 增加 `serve`（缺省子命令保持裸调用兼容）与 `check`（复用 `load_contract`，合法打印摘要退出 0）；`--file` 增加 `--config` 别名；补 3~4 个 CLI 测试即可闭环；
2. 顺手项：banner 单复数、日志时间戳带时区、落 ruff 配置。

**移交下批评测的三个观察点**：
- 批量确认流是否应强制"底牌条款逐条勾选"作为 gate_1 前置（本次 serve/check 漏网的根因）；
- `Argument list too long` 导致 transcript 丢失的 harness 修复验证；
- mattpocock 流与本流的 CLI 命令面 diff（同场景两流产物一个带 check 一个不带，回归成本需量化）。

---

### 附：本报告依据的核验证据索引

- 源码：`src/mock_server/{cli,contract,server,__init__}.py`（全文核读，无截断断点）
- 测试：`tests/{test_contract,test_server,test_cli,conftest}.py`，`grep -c "def test_"` = 22+14+5 = 41
- 依赖：`pyproject.toml`（`dependencies = []`，dev 仅 pytest）
- 过程资产：`.forge/CONTEXT.md`、`.forge/wiki/decision/000{1..4}-*.md`、`.forge/wiki/{index,tags}.md`、`.forge/mock-server/spec.md`、`.forge/tasks/mock-server/state.json`
- 卫生：git 2 commits、工作树干净、0 个 pycache 被跟踪、`.gitignore` 覆盖缓存与 `.claude/`
- 横向参照：`reports/20260925_180113_greenfield-mock_triple_glm-5.3-flashX.md`（mattpocock 13 轮 / tinder_manual 8 轮考评笔记）
