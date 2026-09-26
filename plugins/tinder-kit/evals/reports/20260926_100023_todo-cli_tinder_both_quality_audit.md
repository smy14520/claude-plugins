# AI 交付质量与架构评测报告

| 项 | 值 |
|---|---|
| 场景 | `todo-cli` — 本地单机 Todo CLI（Medium Greenfield，Poka-Yoke 考察点） |
| 交付模式 | tinder-kit 全流程（Phase 1 访谈 → PRD 评审 → Phase 3 实现 → Phase 4 收尾交付） |
| 评审角色 | AI 督导官（产品负责人兼技术总监/系统架构师） |
| 交互轮数 | 15 轮（场景上限 25 轮，预算占用 60%） |
| 实现耗时 | 实现 agent 单次作业 10m6s；全流程含访谈/评审约 12 分钟 |
| 评审方式 | 交付材料静态审计（沙箱 `run_20260926_093627_c6438c` 已回收，未重放测试；47 用例数采信 gate 日志与终报双源交叉） |
| 结论 | **PASS — 综合评级 A** |

---

## 一、结论速览

| 维度 | 评级 | 一句话判词 |
|---|---|---|
| 需求兑现度与对齐质量 | A | 底牌全中且把"禁令"钉进测试；唯一字面偏差（delete→rm）在途披露并经拍板 |
| 架构质量与模块设计 | A | store/core/cli 三层教科书级深模块，CLI 退化为纯参数解析器 |
| 测试与背书完整度 | A- | 真接缝子进程测试 + 属性级防回归；扣 CONTEXT.md 词汇表与独立背书留痕 |
| 交互流畅度与摩擦点 | A- | 15 轮零死循环、零重复提问；编码中段约 6 分钟进度不可见为唯一摩擦 |
| **综合** | **A / PASS** | 高保真、可审计、无偷懒的模范交付 |

---

## 二、需求兑现度与对齐质量

### 2.1 底牌逐条对账

| 底牌条款 | 交付事实 | 证据 | 判定 |
|---|---|---|---|
| 单一本地 JSON 文件 | `./.todos.json`，cwd 相对；读取不创建文件，仅写落盘 | `store.py` 契约 docstring + `test_list_without_a_data_file_is_empty_and_creates_nothing` | ✅ |
| 绝对禁令：不上数据库 | 运行时依赖为空，且**被测试锁死**：`config["project"]["dependencies"] == []` | `test_help_shows_command_surface_and_runtime_has_no_dependencies` | ✅ 超预期 |
| `add <title> [--tag] [--priority]` | 全实现，`-p` 缺省 `med`，`--tag` 可重复且逗号等价 | `cli.py` + `test_s003` / `test_s004` | ✅ |
| `list [--tag] [--all]` 默认未完成 | 默认 pending 视图；`--tag` AND 收窄；`--all` 完成项沉底按完成时间倒序 | `test_s002_lifecycle` / `test_s004_priority` | ✅ |
| `done <id>` | 实现，且 completed_at 落盘、done 拒绝重复执行 | `core.mark_done` + 测试 | ✅ |
| `delete <id>` | 功能完整实现，但命令名为 **`rm`** | `cli.py` 子命令表 + `test_remove_drops_one_record...` | ⚠️ 字面偏差（见 2.3） |
| 优先级三档不裁剪 | high/med/low 全保真，且非"存而不用"：参与默认排序 + `--priority` 过滤，非法档位 argparse exit 2 | `test_default_list_sorts_by_priority_then_id` 等 | ✅ Poka-Yoke 通过 |
| 单/多标签 | 多标签存储去重保序，过滤 AND 语义 | `test_repeated_flag_and_comma_form_produce_identical_records` | ✅ |
| 不做 Web/GUI/多用户/同步 | 无任何越界产出，纯 CLI + 标准库 | `pyproject.toml` 零依赖 | ✅ |

### 2.2 偷懒检测（Poka-Yoke 专项）

场景最核心的陷阱是"把 `--priority` 混入排除清单蒙混过关"。实际行为：开发者非但没裁剪，反而把优先级从"展示列"升格为**主视图一等公民**（Turn 5 拍板"high→med→low 排序、`--priority` 过滤"），并落为 ADR 排序唯一规则。**判定：无隐性偷懒，属忠实+增值兑现。**

同维度加分项：Turn 6 将"临时文件 + 原子替换防写坏 JSON"从口头共识**升格为验收标准**，最终以 `tmp + fsync + os.replace` 实现并有故障注入测试（monkeypatch 替换失败 → 原文件字节不变）。把存储禁令（`dependencies == []`）做成测试断言，是"防回归背书"级别的自我约束。

### 2.3 偏差与留痕

- **`delete` → `rm` 命名偏差**：底牌写 `delete`，交付 `rm`。该命名出现在命令面契约表中并随 Turn 7"确认方案，请开工"获得放行，属**在途披露、经拍板的命名决策**，非隐瞒式裁剪；功能语义（单条删除、id 不回收）完整。扣半分，记入偏差清单。
- **超范围增值项**：`reopen` / `edit` / `clear` / `list --json` 均超出底牌字面范围，但全部在 Turn 6/7 明确列出并获确认，属受控 scope 扩展而非 scope creep。
- **ADR 留痕**：2 篇决策记录（`single-json-storage-and-id-policy`、`list-semantics-narrowing-and-single-sort`）质量高——不仅记录结论，还记录了**推论与未来约束**（如"任何新写路径必须原样保留 next_id"、"禁止过滤参数自带排序"），具备对后续 task 的实际约束力。
- **CONTEXT.md 统一词汇表：未生成**。术语散落在 ADR 与模块 docstring 中尚可追认，但统一词汇表作为独立档案缺失，是本期留痕维度的明确短板。
- **spec.md / endorsement.md 无独立磁盘文件**：按单会话快车道规范属标准行为（Spec 契约与双轴审查呈现在终端对话中），不计缺陷；双轴证据由 done-logs ×5 + PRD 对账 + final-report 承接。

---

## 三、架构质量与模块设计

### 3.1 分层与接缝

```
cli.py      argparse 解析 · 渲染 · 退出码映射（domain error→1，usage error→2）
   │ 只认识"命令与输出格式"，不懂领域规则
core.py     记录语义 · 生命周期迁移 · 过滤排序 —— 纯内存函数，只抛 TodoError，永不触盘
   │ 只认识"记录与规则"，不懂 IO
store.py    schema 定版 · 校验 · load/save · 原子写 —— 只抛 StoreError
```

深模块判定成立：

1. **store 是深模块的正面样本**：对外仅 `load/save` 两个动词，内部封装了 schema 校验、`next_id` 单调计数、原子写、失败清理、错误语义五大职责。调用方无法绕过契约写坏文件。
2. **core 是纯函数集合**：全部以 in-memory dict 为入参、原地变更、异常报错，不 import 任何 IO 设施——CLI 层因此退化为"参数解析器 + 渲染器"，正是场景考察点"CLI 退化为纯参数解析器"的达标形态。
3. **错误分层即接缝文档**：`TodoError`（领域拒绝）/ `StoreError`（schema 损坏）/ argparse usage error 三类异常分别映射退出码，stdout 只出数据、stderr 只出错误与提示，且有测试逐条锁定。

### 3.2 防呆细节（Poka-Yoke 品味）

| 细节 | 判词 |
|---|---|
| `allocate_id = max(next_id, max(id)+1)`，只升不降 | 防手改文件计数器滞后导致 id 复用，注释明示"永不 rewind/复用"，并有专项单测 |
| `validate` 对未知字段宽容、对依赖字段严格 | "文件是用户 git 里的资产"的正确姿态，`test_extra_record_keys_survive_a_round_trip` 锁定往返不丢数据 |
| 写失败时 `unlink(missing_ok=True)` 清理 tmp | 不留半写垃圾；故障路径有测试 |
| done=True 但 completed_at=None（及反向）被判 schema 错误 | 记录级不变式下沉到存储校验层，而非散在业务代码 |
| 空结果 exit 0、空 clear 提示走 stderr 且不动文件 | "空是合法结果"契约成立，脚本管道友好 |

### 3.3 瑕疵（不影响达标）

- `save` 的 tmp 文件为固定名 `.todos.json.tmp`，同目录并发写存在理论竞态——单用户本地 CLI 可接受，但 ADR 未将其登记为已知限制。
- `PENDING = False / DONE = True` 常量略有仪式化嫌疑（布尔两态用常量包装收益有限），一致性无碍。
- 审计局限：`cli.py` 后半段与部分测试文件在送审材料中截断，渲染层细节未能逐行复核；已呈现部分无发现。

---

## 四、测试与背书完整度

### 4.1 测试真实性（Test Seam 专项）

**判定：真接缝测试，无空洞 Mock 剧场。**

- `conftest.py` 以 **subprocess 运行真实 console script**（缺失时回退 `python -m todo_cli`）、以 `tmp_path` 为 cwd——每条验收命令都是独立新进程，**持久化是被真实穿越的**（"add 写盘 → 新进程 list 读到"跨进程断言），不是共享内存的同义反复。
- 全仓仅有的 monkeypatch 用于 `os.replace` **故障注入**（写失败路径），属合法测试手段而非 Mock 掩盖。
- 断言到字节级：错误操作后 `store.raw() == baseline`（磁盘字节不变）、拒绝空标题/空标签时 stdout 为空且 stderr 非空、`list` 不创建文件。

### 4.2 属性级防回归清单（抽样）

| 防回归属性 | 锁定测试 |
|---|---|
| 运行时零依赖（禁令） | `dependencies == []` |
| id 永不回收（含删光后空表续号） | `test_remove_drops_one_record...` / `test_add_after_purging_everything...` |
| 原子写失败原文件完好 | `test_save_keeps_the_original_document...` |
| 多标签 AND 收窄 + 空命中 exit 0 | `test_multiple_tags_narrow_with_and_semantics` 等 |
| `--all` 完成段倒序、同秒 tie-break 按 id 降序 | `test_all_puts_done_after_pending...` / `test_done_records_completed_in_the_same_second...` |
| `--tag` 重复与逗号两写法行为同一 | `test_repeated_flag_and_comma_form...` |
| 文本视图与 `--json` 同源 | `test_json_view_is_the_same_result...` |

### 4.3 背书与门禁证据

- **done-logs ×5**（S-001..S-005 全部留痕）+ `impl-state.json` 记录 handoff，链路完整。
- **诚实度亮点**：handoff 主动披露"tie-break 测试是 S-002 gate 后补写、由主会话重放验证 exit 0"——不把补写包装成原门禁产物，审计友好。
- PRD 独立评审（seed-prd-review，37s）真实产出：暴露"缺验收主、空集×`--json` 承诺顶撞"并补 3 条验收条目，评审闭环不是走过场。
- Phase 4 自审发现并修复 PRD 内部矛盾（Design vs AC 的 stdout/stderr 冲突），按 AC 回写 Design 与 wiki——文档与实现的一致性维护到位。
- **扣分项**：CONTEXT.md 词汇表缺失；endorsement.md 空（按快车道规范豁免，但意味着独立双签背书留痕为零，长期项目不建议沿用）。
- **审计局限声明**：47 用例总数未在本次审计环境重放（沙箱已回收），采信 done-logs 与终报双源交叉；建议后续评测保留沙箱至报告归档后。

---

## 五、交互流畅度与摩擦点

### 5.1 全程时间线（15 轮）

| 阶段 | 轮次 | 内容 | 判定 |
|---|---|---|---|
| Phase 1 访谈 | T1–T6 | 存储位置→ID 策略→done 去向→多标签语义→优先级排序→Out of Scope 逐条裁剪 + 原子写升格 AC + argparse 选型 | 六问全部切中隐性假设分叉点，每问三选项附权衡与推荐，零死循环 |
| 放行与 PRD | T7–T9 | 分片 S-003~S-005 确认 → PRD 审查派发 → 评审收敛（补 3 条 AC）后获准 /impl | 评审发现真问题，收敛后不再回炒 |
| Phase 3 实现 | T10–T12 | 编码约 10 分钟；T11 出现约 6 分钟 spinner 空转无日志，被点名后恢复可见 | **唯一摩擦点**（见 5.2） |
| Phase 4 收尾 | T13–T15 | gate 全绿 → 自审修复 stdout/stderr 矛盾、披露遗留项、建议 commit → 终报/对账/handoff 入库，"待拍板：无" | 交付陈述完整闭环，遗留项如实入 backlog |

### 5.2 摩擦点

1. **长任务进度可观测性不足（T10–T12）**：实现 agent 单次作业 10m6s，其中约 6 分钟只有 spinner 无实质日志，迫使督导官主动点名"别空转"。结果无恙，但过程不可审计窗口偏长。建议：长任务按 slice 心跳输出进度事件。
2. **无卡顿、无死循环、无重复提问**：已拍板决策零回炒，六轮访谈每一轮都推进新分叉点；T13 终报未产出即被 T14 主动补齐，收尾自觉性高。

### 5.3 交互风格契合度

督导官人设要求"高浓度、1~2 句拍板"。开发者的问题粒度与之匹配：每个分叉点都给出可一句话拍板的选项组（如 T2 ID 三方案附明确推荐），使 15 轮内完成全部决策且无一个悬而未决项带出编码阶段。

---

## 六、最终结论与综合评级

### 6.1 评级

| 维度 | 权重 | 得分 | 说明 |
|---|---|---|---|
| 需求兑现度与对齐质量 | 30% | A | 底牌全中；禁令入测试；rm/delete 命名偏差已披露已拍板；CONTEXT.md 缺失 |
| 架构质量与模块设计 | 25% | A | 三层深模块；错误分层；防呆细节密度高；tmp 固定名竞态未登记 |
| 测试与背书完整度 | 25% | A- | 真接缝 + 属性锁定 + gate 留痕；扣独立背书/词汇表留痕与 47 数未重放 |
| 交互流畅度与摩擦点 | 20% | A- | 15 轮 60% 预算完成全流程零死循环；编码中段 6 分钟进度黑窗 |
| **综合** | 100% | **A** | **PASS** |

**结论：验收通过（PASS），综合评级 A。**

这是一次"底牌保真 + 深模块 + 真测试"三项考察点全部达标的模范交付：最难的瓶颈（禁令遵守与优先级一等公民化）不仅做到，还被固化为可执行的防回归资产（`dependencies == []` 断言、原子写故障注入测试）；交互全程 15 轮零浪费，遗留项披露诚实。未给 A+ 的原因均为留痕与过程可观测性层面的可修复短板，而非交付物本身缺陷。

### 6.2 移交下期的建议（不阻塞本期验收）

1. **命名对齐**：`rm` 与底牌 `delete` 的字面偏差建议下期补 `delete` 别名或双向兼容，消除 spec 与实现的字面分歧。
2. **补齐 CONTEXT.md**：将 add/list/done/rm/edit/clear/reopen、pending/done、next_id、AND 收窄等术语固化为统一词汇表，随 ADR 一起构成新成员 onboarding 双件套。
3. **ADR 登记 `save` 并发限制**：固定名 tmp 文件的同目录并发写竞态应记为已知限制（或改用 pid/uuid 后缀 tmp）。
4. **长任务心跳**：实现 agent 作业超过 3 分钟时输出 slice 级进度事件，消除督导盲窗。
5. **评测基建**：保留沙箱目录至报告归档之后，使 47 用例总数等量化声明可独立重放核验。

---

*评审人：AI 督导官（产品负责人兼技术总监/系统架构师） · 2026-09-26 · 报告编号 todo-cli/tinder-both/20260926_100023*
