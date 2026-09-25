# 自动化双角色评测大盘 — todo-cli

- 时间: 2026-09-25T11:42:34.477937
- 渠道配置: ccz
- 模式: treatment

## 实验组 (tinder-kit) 评测报告

`rm` 也被会话策略拒绝了——重建目录将保持原样并被公开。我现在已准备好所需的一切：完整的源码级核查、历史场景报告中的纵向证据（`evals/reports/` 中 6 轮和 9 轮的既往运行记录），以及产物取证。以下是报告。

---

# 《AI 交付质量与架构评测报告》— Todo CLI（tinder-kit 单切片快车道）

**评测对象**：Todo CLI（`todo/` 包：model / store / filters / cli / `__main__`，Python 3.12，纯 stdlib）
**运行模式**：单切片快车道直通实现（Spec 契约呈现于终端对话记录）
**评测日期**：2026-09-25 ｜ **评审人**：AI 督导官（资深技术总监 / 系统架构师）
**证据基线**：① 全程 4 轮人机交互监控记录；② 交付物完整文件清单（含 git 对象、pytest 缓存、pyc 时间戳）；③ 核心代码与测试全文（4 源文件 + 5 测试文件）；④ CONTEXT.md、ADR-0001、state.json 全文；⑤ 本场景历史 run 归档报告（`evals/reports/`，用于纵向对照）。

> **取证方法披露**：本轮尝试以证据包全文重建工程并独立复跑 pytest，因会话执行策略禁止运行 Python/测试进程未能成行（与本场景既往 run 遭遇的同一策略限制）——故运行时结论采用**逐行静态追踪 + 产物痕迹交叉验证**：32 个测试逐一推演全部可到绿；`tests/__pycache__/` 下恰有 5 个测试模块的 `cpython-312-pytest-9.0.3.pyc`，且 `.pytest_cache/v/cache/` 同时存在 `nodeids` 与 **`lastfailed`**——后者是 TDD 红轮真实发生过的物证，与 state.json 自述"1 轮红为测试脚手架缺陷（capsys 排水 + subprocess PYTHONPATH）"互洽。复核用重建工程暂存于仓库 `.tmp-review/todo-cli-eval/`（清理指令未获会话授权，可安全手动删除）。
>
> **规范说明**：单切片快车道下无独立 spec.md / endorsement.md 磁盘文件属标准行为（契约与背书由终端对话 + state.json 承载），依规不判档案缺失。

---

## 一、需求兑现度与对齐质量 — **9.2 / 10（A）**

### 1.1 底牌红线逐条核查

| 底牌要求 | 兑现情况 | 代码级证据 |
| :--- | :--- | :--- |
| 本地**单一 JSON 文件**存储 | ✅ 完全兑现 | `cli.DEFAULT_STORE_NAME = ".todos.json"`（cwd 即项目根），schema `{"next_id", "todos"}`，`ensure_ascii=False, indent=2` 人类可读 |
| **绝对禁令**：无 SQLite / 任何数据库 | ✅ 零触碰 | 全部 import 仅 `argparse/json/os/sys/tempfile/datetime/pathlib/dataclasses/enum`，零第三方运行时依赖；ADR-0001 书面否决 SQLite |
| `add <title> [--tag] [--priority high\|med\|low]` | ✅ 签名对齐 | `title nargs="+"` 多词拼接；`--tag` 可重复（单/多标签天然支持）；`choices=[high,med,low]` argparse 强校验，默认 `med` |
| `list [--tag] [--all]` 默认只列未完成 | ✅ | `filter_todos` 默认排除 Done；多 `--tag` AND 语义（子集匹配） |
| `done <id>` | ✅ | 置位 Done 并落盘；未知 id → stderr + exit 1（有测试钉死） |
| `delete <id>` | ⚠️ 语义✅ / 命名漂移 | 实现为 **`rm`**，删除语义完整、幂等落盘；字面命令名与底牌不符（详见 I1） |
| 不做 Web/GUI、多用户、跨机同步 | ✅ 零蔓延 | 无任何 socket/http/server 代码；命令面恰好 4 个子命令 |

**三条下游裁定的落地追踪**（Turn 1 拍板的原子写 / id 永不复用 / list 默认语义）——全部形成"裁定 → 代码 → 回归测试"闭环，这是本轮留痕质量的最佳证据：

| 裁定 | 代码 | 回归测试 |
| :--- | :--- | :--- |
| 临时文件 + `os.replace` 原子写 | `store.save()`：`mkstemp` → 写 → `os.replace`，异常路径 `unlink` 清理残留 | `test_atomic_write_leaves_no_temp_files` |
| id 单调递增永不复用 | `next_id` 计数器**持久化在文件内**（ADR 记录了动机：`max(id)+1` 推导会在删最大号后复用） | `test_id_never_reused_after_removing_max` |
| list 默认隐藏 Done，`--all` 显全部 | `filters.filter_todos` | 2 个 filters 测试 + 2 个 CLI 测试 |

### 1.2 统一语言与决策留痕

- **CONTEXT.md** ✅ 上乘：Todo / Tag / Priority / Filter / Store / Done 六术语各配定义与 **_Avoid_ 负面清单**（如 Tag 禁漂移到 label/category，Done 与 rm 的语义分工显式立法"两者互不替代"）。且词汇表**真被消费**：`model.py` docstring 显式回链 `.forge/CONTEXT.md`，`filters.py` docstring 原文使用"Tag … AND, Done hidden by default"，CLI help 文案用 `Tag`/`Done`/`Priority level`，测试命名（`test_multiple_tags_on_cli_are_and`、`test_done_hides_todo_from_default_list`）同样按词汇表命名——活文档，非装饰。
- **ADR-0001** ✅ 教科书级：拍板结论（项目根单 JSON + next_id 落盘 + 原子写）、三个被否决选项（SQLite 过度设计且违"零数据库"裁定、`~/.todo-cli/` 全局清单身份错配、裸数组无法保证 id 永不复用）、Consequences（`cat .todos.json` 即可审计）、Revisit 触发器齐备，并记录了否决理由的**机理**而非仅结论。
- **背书链**：快车道无 endorsement.md 依规不扣分；Turn 4 业主验收（"验收通过，本次交付正式收官"）+ `state.json phase=COMPLETED` 构成对话背书。超范围诉求（编辑标题、duedate、undo）**规范沉淀进 `issue-tracker.md` 而非私自扩张**——范围纪律满分。
- **证据包留白（非缺陷）**：`state.json` 内容在"Final: 32 pass"处截断、`domain.md`/`triage-labels.md`/`issue-tracker.md`/`wiki/*` 仅见于清单未随卷内容、`pyproject.toml` 内容未附——均属证据呈现层面的缺口，不影响判定。

### 1.3 发现项

- **I1【低】`delete` 被实现为 `rm`（字面命令名漂移）**：删除语义完整且被词汇表显式锚定（"rm 才是删除"），但底牌写的是 `delete`。值得注意的细节是：Turn 4 业主验收话术说的也是"add/list/done/delete"——**双方在验收时刻都滑过了这个漂移**，说明它从未获得显式批准，属"词汇表自我立法覆盖了底牌字面"的低风险漂移。一行可修：`sub.add_parser("rm", aliases=["delete"])`。

**小结**：无隐性偷懒、无功能残缺、无范围蔓延、零红线触碰；唯一字面偏差 I1。

---

## 二、架构质量与模块设计 — **9.0 / 10（A）**

### 2.1 拓扑：四模块单向依赖，深模块 × 薄接缝成立

```
cli.py (薄壳：argparse 装配 + 渲染 + 退出码，零持久化知识)
   ├── filters.py (纯函数查询：Tag AND + Done 门控，零 IO、零状态)
   └── store.py   (深模块 Store：接口仅 load/save/add/complete/remove，
   │                封装文件格式、schema、id 分配、原子写与残留清理)
   └── model.py   (冻结值对象 Todo + Priority 枚举，自持序列化)
```

- **深模块判据达标**：`Store` 接口五个动词，内部隐藏了 tmpfile 命名、`os.replace` 时机、异常清理、`next_id` 维护——调用方（CLI）对持久化机制零感知；复杂度被吞进模块而非泄漏到接缝。
- **接缝可注入性（本轮最大架构进步）**：`main(argv, store_path)` 与 `Store(path)` 双注入点 + `filter_todos` 纯函数，使 32 个测试**零 monkeypatch、零 chdir** 即得完全隔离。对照本场景归档的上一轮 treatment run 被判 B+ 的两条核心扣分——"CWD 相对路径且无注入口"与"非原子覆写"——**本轮全部修复且各有测试钉死**，外加 `test_python_dash_m_entrypoint_runs_in_cwd` 用子进程把 `python -m` 入口与 cwd 隔离一并钉住。这是对历史评审意见的精准响应。
- **单一事实源**：Priority 三档唯一定义于枚举（argparse choices 由枚举推导，非手抄字符串）；AND 语义唯一定义于 `set ⊆` 一处；渲染唯一定义于 `_render`。
- **规模克制（YAGNI）**：无 repository 抽象、无插件层、无 config 系统；`created_at` 用 ISO 字符串而非 datetime 对象——对单机个人工具是正确的减法。

### 2.2 瑕疵与改进空间（均不阻塞验收）

1. **I3【低-中】损坏 JSON 无定义行为**：`Store.load` 对非法 JSON 直接 `json.loads` 裸抛 `JSONDecodeError` → 终端 traceback。ADR-0001 的卖点之一是"人类可读、**可手改**"，手改就必然有改坏的场景——静态追踪确认此路径既无友好报错也无测试。应在 load 处捕获并输出 `Error: corrupt store file` + exit 1，并补一条测试（上一轮 0923 run 的 `test_corrupt_json_raises` 正是范本）。
2. **I4【微】`complete()` 手工逐字段重建 Todo**：既然 `Todo` 是 frozen dataclass，`dataclasses.replace(todo, done=True)` 一行等价且免于"加字段时漏抄"的演化风险。
3. **I5【微】`os.replace` 前无 `fsync`**：极端断电下 rename 先于数据块落盘可能产生空文件。此量级的个人工具可接受，建议在 ADR 的 Consequences 里明示为已知权衡（已声明的债务不是隐性债务）。
4. `--tag` 的 `default=[]` 可变默认值因 `build_parser()` 每次 main 调用新建而不致泄漏——当前无风险，属知晓即可的细节。

---

## 三、测试与背书完整度 — **9.0 / 10（A）**

### 3.1 套件构成与静态追踪结果

**32 个测试逐一静态推演，全部可到绿，与 state.json"32 pass"自述一致**：

| 文件 | 数量 | 钉住的规约 |
| :--- | :--- | :--- |
| `test_model.py` | 5 | Priority 默认 MED / 三档解析 / 拒绝非法值（带友好报错）/ 序列化往返 / list→tuple 归一化 |
| `test_store.py` | 8 | 空文件语义 / 存取往返 / **schema 形状**（`set(data)=={"next_id","todos"}`）/ **原子写零残留** / **id 删最大号后不复用** / complete 持久化 / remove 返回值 / 未知 id KeyError |
| `test_filters.py` | 7 | 默认隐藏 Done / show_all / 单标签超集匹配 / **多标签 AND** / 组合行为 / 空结果 |
| `test_cli.py` | 12 | add↔list 往返 / 过滤排除 / CLI 层 AND / done 隐藏 / --all / rm 永久 / 多词标题拼接 / 默认 med / **非法 priority SystemExit≠0** / **未知 id exit 1 + stderr** / 空清单占位 / **子进程级 `python -m` cwd 隔离 e2e** |

**测试哲学正确**：断言写的是**规约**（"永不复用"、"零临时残留"、"退出码 + stderr 通道"）而非实现快照；测试钉在接缝上（注入 `store_path`、直调 `main(argv)`），重构内部实现不会误伤。物证链完整：5 个测试模块的 pyc + `nodeids` + `lastfailed`（红轮为真，且 state.json 诚实披露红因系**测试脚手架自身缺陷、只修了测试**——这份不粉饰的记录本身就是工程操守证据）。上一轮 0923 run 被点名"CLI 层无 e2e"的缺口，本轮以进程内 main 直调 + 子进程入口测试补齐。

### 3.2 缺口（按值得补的顺序）

- 损坏 JSON 行为未测且未定义（I3，与测试缺口互为表里）；
- `_render` 输出格式（`#tag`、`(high)` 呈现）无逐字断言——CLI 契约的最后一小块；
- `pip install -e .` 的 console-script 入口因 `pyproject.toml` 内容未随卷无法核验（`python -m` 入口已验证）；
- 无 CI 挂钩（单机项目可谅解）。

### 3.3 背书链

快车道规范下以 Turn 4 对话验收 + `state.json` COMPLETED 为背书，依规成立；超范围诉求入 `issue-tracker.md` 形成后续切片队列，审计链完整。

---

## 四、交互流畅度与摩擦点 — **9.5 / 10（A）**

**全程 4 轮收官，零死循环、零卡顿、零空转**——为本场景历史 run 中最短路径（对照归档：上一轮 6 轮、再上一轮 9 轮）：

| 轮次 | 阶段 | 质评 |
| :--- | :--- | :--- |
| T1 | 访谈 + 裁定 | 批量澄清隐性假设（stdlib/pytest/3.12/边界），提问带推荐方案。**唯一红旗：Q7 试图把优先级排除出 v1**——需求漂移未遂，业主当轮按底牌拍死，此后零复发 |
| T2 | 开工确认 | 先沉淀 CONTEXT.md + ADR-0001 再动码，顺序正确；选型与底牌逐句对齐 |
| T3 | 编码收尾 | TDD 红绿完成；**主动自查** `git add -N` 误扫 `__pycache__`/`.pytest_cache` 并清理，运行时数据 `.todos.json` 声称已入 `.gitignore` |
| T4 | 审查交付 | 双轴审查收敛为可选打磨项（S1–S5/c1/c2 不阻塞）；用法文档 + COMPLETED 总结；超范围诉求规范入 issue-tracker |

**摩擦点统计**：需求分歧仅 T1 一次且单轮收敛；沟通成本 4 拍（裁定 / 鼓励 / 认可 / 验收），每轮答复均被精准消费无重复提问。

- **I2【低】留痕与产物的轻微失配**：T3 称已将 `.todos.json` 纳入 `.gitignore`，但交付文件清单（工作树快照，含 `.pytest_cache`、`.forge`、`.git` 等全部点文件/点目录）中**未见 `.gitignore`**。若确缺，克隆后跑一次测试即污染 git status；一行可补。也不排除证据包快照时序差异，故按"待核验的低风险失配"记录，不升格为缺陷。

---

## 五、最终结论与综合评级

| 维度 | 得分 | 等级 | 一句话判词 |
| :--- | :--- | :--- | :--- |
| 需求兑现度与对齐质量 | 9.2 | A | 底牌逐条兑现、零数据库红线零触碰；裁定→ADR→测试全链闭环，唯 `delete→rm` 字面漂移 |
| 架构质量与模块设计 | 9.0 | A | 深模块薄接缝成立、双注入点可测性极佳；历史扣分项（路径注入、原子写）全部修复；损坏 JSON 无定义行为是唯一实扣 |
| 测试与背书完整度 | 9.0 | A | 32/32 面向接缝的规约级测试 + 子进程 e2e + 真实红轮留痕；corrupt-file 与渲染契约留白 |
| 交互流畅度与摩擦点 | 9.5 | A | 4 轮最短路径收官，漂移未遂单轮拍死，卫生自查主动 |
| **综合** | **91.5 / 100** | **A** | |

### ✅ 最终判定：**PASS — 评级 A**

**一句话总评**：这是一次"底牌忠实兑现 + 裁定全链可追溯 + 接缝先行的 TDD 交付"——存储禁令零触碰、三条下游裁定各有代码与回归测试双重钉死、历史 run 的全部已知短板（无测试、路径不可注入、非原子写、CLI 层无 e2e）在本轮一并清偿，且以本场景迄今最少的 4 轮沟通成本完成。它没拿到 A+ 的原因全部是一行级修复：命令名字面漂移、损坏 JSON 无定义行为、`.gitignore` 留痕失配。

**遗留改进建议（按优先级，均不阻塞已完成的验收）**：
1. `rm` 补别名 `sub.add_parser("rm", aliases=["delete"])`，对齐底牌字面命令名（I1）；
2. `Store.load` 捕获 `JSONDecodeError` → 友好报错 + exit 1，并补测试，兑现 ADR"可手改"口径（I3）；
3. 核验并落盘 `.gitignore`（`.todos.json` / `__pycache__` / `.pytest_cache`）（I2）;
4. `complete()` 改用 `dataclasses.replace(todo, done=True)`（I4）；
5. 补 `_render` 输出契约断言；ADR 补记"无 fsync"为已知权衡（I5）。

---

*附注：本次评审的动态复跑被会话执行策略阻断，已如实披露并以静态追踪 + 产物取证替代；重建复核工程位于 `.tmp-review/todo-cli-eval/`（删除指令未获授权，内容与证据包逐字一致，可安全手动删除）。*

