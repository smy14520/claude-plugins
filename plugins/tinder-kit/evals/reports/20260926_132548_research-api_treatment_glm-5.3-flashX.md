# 自动化多角色评测大盘 — Release-Watch: 依赖外部 API 事实的小工具 (research-api)

- 场景类型: e2e
- 时间: 2026-09-26T13:25:48.525484
- 渠道配置: zhipu-glm
- 评估模型: glm-5.3-flashX
- 测试组: tinder_develop

## 各方案独立质检报告

### Tinder-kit develop 自动编排流 (tinder_develop)

所有取证完成：工作树干净、代码与测试齐全、`.forge` 档案结构已核对。以下是正式评测报告。

---

# 《AI 交付质量与架构评测报告》

| 项目 | 内容 |
|---|---|
| **交付物** | `release-watch` — GitHub 正式 Release 查询 CLI（单文件 Python 标准库实现） |
| **评审对象** | 工作区 `/private/tmp/.../tinder_develop`（commit `6a9a4dc`，工作树 clean） |
| **评审日期** | 2026-09-26 |
| **评审方式** | 代码静态取证 + 测试断言逐条人工验算 + 全程交互记录交叉验证。*注：本评审沙箱仅放行只读命令，测试套件无法由评审方现场复跑，相关运行结论引自交付过程记录（Turn 4/5），并已对全部断言数学做了静态人工验算。* |

---

## 一、需求兑现度与对齐质量 —— ★★★★☆（4.5/5）

### 1.1 底牌逐条核对

| 底牌要求 | 兑现情况 | 证据 |
|---|---|---|
| `release-watch <owner/repo> [-n N]`，默认 N=5 | ✅ 完整兑现 | `argparse` 位置参数 + `-n/--number` default 5；另有 OWNER/REPO 格式校验（exit 2），超出底牌的健壮性加分 |
| REST `/repos/{owner}/{repo}/releases` + `per_page` 分页 | ✅ 完整兑现 | `make_fetch_page` 拼接 `per_page=100&page=N`，客户端翻页取够 N 即止（有测试断言 `requested == [1]` 防止过量请求） |
| 正式 release 排除 `draft`/`prerelease` | ✅ 完整兑现 | `is_official()` + 专项测试 |
| 403/429 限流 + `GITHUB_TOKEN` | ⚠️ 基本兑现，一处软肋 | 403 → 友好提示并建议设置 `GITHUB_TOKEN`；token 经 `build_request` 挂 Bearer 头、静默不打印（有测试）。**软肋：429 落入通用 `HTTP {}` 分支，仍有单行报错+exit 1，但丢失了 token 提示语**，对底牌"403/429 同类处理"的还原欠一刀 |
| 仓库不存在返回 404 | ✅ 完整兑现 | `RepositoryNotFound` 在 `make_fetch_page` 闭包内被富化为 `repository 'owner/repo' not found`，报错含上下文 |
| 只用标准库 | ✅ 完整兑现 | 全部 import 为 `urllib/json/datetime/argparse/os/sys/unittest`，零第三方依赖 |
| 测试离线 + 可替换 Seam | ✅ 完整兑现 | 见第三节 |
| 输出 tag + YYYY-MM-DD + 距今天数 | ✅ 完整兑现 | UTC 格式化 `strftime("%Y-%m-%d")`；天数 floor 语义、未来时间戳钳 0，均有测试钉死 |
| Out of Scope（无 Web/缓存/GitLab） | ✅ 无越界 | 代码中无任何越界实现；`state.json` 明确记录 6 条 out_of_scope |

### 1.2 词汇表与决策留痕

- **CONTEXT.md 统一词汇表 ✅**：`.forge/CONTEXT.md` 收录三个核心术语（正式 Release / 发布时刻 / 距今天数），各带 `_Avoid_` 负面清单。更难得的是**词汇表与代码标识符严格对齐**：`is_official`、`published_at`、`age_in_days` 直接来自词汇表，术语未在实现中漂移——统一语言真正落到了代码里，而非装饰性文档。
- **ADR ❌（轻微）**：`.forge/wiki/decision/` 未创建，无正式 ADR 文件。缓解因素：`state.json` 的 `decisions` 数组以 Q1–Q7 形式完整记录了全部七个契约决策及理由（含“3.8 的 `fromisoformat` 不认 Z 后缀需手工处理”这类有价值的 trap 记录）。对单文件工具，决策日志实质等效于轻量 ADR，扣分但不致命。
- **诚实披露 ✅**：开发者主动声明两项遗留——测试未纳入 mypy strict、本机 3.12 验证建议 3.8 复跑。代码层面 3.8 兼容是真实落地的（`from __future__ import annotations` + 手工 `Z→+00:00`），非遗留口头支票。

### 1.3 超出底牌的加分项

- `urlopen` 带 30s timeout（防吊死）；
- 响应体非 JSON / 非数组双重防御（commit `45b1d1e` 显示这是两轴评审揪出后补的，修完补了测试）；
- 排序锚定 `published_at` 且**客户端重排**——正确识别了 API 列表按 `created_at` 排序、草稿晚发布会干扰"最近"语义的陷阱，这是对 GitHub API 契约的真实查证而非凭记忆。

---

## 二、架构质量与模块设计 —— ★★★★★（5/5）

这是本次交付最亮眼的部分，教科书级的**深模块 + 薄接缝**分层：

```
┌─ CLI 壳层 ──────────── main(argv, make_fetch_page=?, now=?)   ← 三个可注入点
├─ HTTP 边缘 ─────────── make_fetch_page → fetch_json → build_request → urlopen
└─ 纯核心 ────────────── collect_official / is_official / parse_iso8601
                         / age_in_days / format_table            ← 零 I/O 依赖
```

- **接缝设计**：`collect_official(fetch_page: Callable, limit)` 只依赖一个函数签名；网络边界收缩为单点 `make_fetch_page`，`main` 再以默认参数形式暴露它——默认值即生产实现，注入即测试替身，**接缝薄到只剩一个类型标注**。
- **时钟也是接缝**：`now: datetime | None` 参数让“距今天数”完全确定性可测，这是很多资深工程师都会漏掉的一刀。
- **依赖方向干净**：核心五个纯函数不 import 任何 I/O 模块；错误体系两级（`ReleaseWatchError` 基类 + `RepositoryNotFound` 子类），404 富化逻辑放在拥有 owner/repo 上下文的闭包内，职责落点准确。
- **内聚性**：每个函数单一职责，`fetch_json` 把三类失败（HTTPError/URLError/坏响应体）归一为领域异常，正是“错误在边缘翻译、核心说领域语言”的正确做法。
- 微瑕（不影响评级）：`main` 的 `make_fetch_page` 默认参数遮蔽模块级同名函数，是惯用 DI 手法但对初读者稍隐晦；仅捕获 `ReleaseWatchError` 意味着违反 API 契约的畸形 release 条目会裸 traceback——在“信任 API 契约”的定位下可接受。

**结论：高内聚、低耦合、依赖单向，深模块典范。**

---

## 三、测试与背书完整度 —— ★★★★☆（4/5）

### 3.1 离线性验证（静态取证）

全文件 23 个用例，**无一触及真实网络**，双层隔离：
- 核心层用 `FakePager` 替身 `fetch_page` 接缝；
- HTTP 层 `mock.patch("release_watch.urlopen", ...)` 在模块边界拦截，连 URL 拼接与 Accept 头都断言到位；
- CLI 层经 `main(make_fetch_page=..., now=...)` 注入，stdout/stderr 全量断言。

### 3.2 断言质量（人工验算）

抽样验算全部通过：`2026-09-25 12:00 → 2026-09-26 12:00` 恰好 1 天 ✅；`13:00 → 次日 12:00` 23 小时 floor 为 0 ✅；`main` 用例 `6天12小时 → DAYS_AGO=6` ✅；交付演示 `2026-05-14 → 134 天`（5/14→9/26 日历 135 天，含时刻偏移 floor 为 134）内部自洽 ✅。覆盖面包括：draft/prerelease 过滤、取够即停（防过量请求的 `requested` 断言是亮点）、翻页穷尽、Z/offset 双格式解析、token 挂/不挂、404/403/URLError/非 JSON/非数组五条错误路径、无正式 release 的专项 exit 1、malformed 参数 exit 2、环境变量 token 透传。

### 3.3 防回归背书

- 无独立 `endorsement.md`——按单会话快车道规范属标准行为，不作缺陷计。
- 防回归背书由 **23 例测试套件 + Git 历史**承担：`feat → fix(45b1d1e 坏响应体契约) → chore` 提交序列显示评审循环真实起效、问题修复伴随测试，且工作树 clean、交付已落提交。

**保留意见**：本评审沙箱无法复跑套件（执行策略限制），23 例的“全绿”结论采信自过程记录；静态验算未发现任何断言错误，可信度高但非评审方亲测。另 429 无专属测试。

---

## 四、交互流畅度与摩擦点 —— ★★★★☆（4/5）

**全程 5 轮收敛**，节奏：T1 七问批量访谈收尾 → T2 产品决策拍板+开工令 → T3 实现 → T4 双轴评审 → T5 交付总结+真机演示+交还。

- **事实查证焦点 ✅ 达标**：限流额度（60→5000/时）、`per_page`、`draft/prerelease` 字段、`created_at` 排序陷阱等 API 事实全部由开发者自行查证后给出方案，**没有一次把 API 细节甩回给用户**——用户在 T2 明确说“API 细节你自己查官方文档”，开发者做到了。
- **无死循环**：T3 终端出现 `Retrying attempt 6~7/10` 系基础设施层重试噪声，逻辑层未陷入循环，T4/T5 按时序正常推进至闭环。
- **摩擦点**：① T2 大量 spinner 噪声掩盖了实质进度，旁观者需靠追问确认状态（观感问题）；② T2 需用户主动下达“开工”指令才推进，主动性可再进一步；③ 全程仅 5 轮、每轮有实质产出，整体效率在同类协作中属上乘。

---

## 五、最终结论与综合评级

| 维度 | 得分 | 一句话评语 |
|---|---|---|
| 需求兑现与对齐 | 4.5/5 | 底牌全兑现，429 提示语与 ADR 缺位是仅有的两处软肋；词汇表与代码标识符严格同源是惊喜 |
| 架构与模块设计 | 5/5 | 纯核心/HTTP 边缘/CLI 壳三层单向依赖，连时钟都是接缝，深模块典范 |
| 测试与背书 | 4/5 | 23 例全离线、断言经人工验算无误、评审循环真实起效；扣在评审方无法复跑 + 429 无专属用例 |
| 交互流畅度 | 4/5 | 5 轮收敛、API 事实全程自查、无死循环；spinner 噪声与等待开工令是小摩擦 |

### 🏆 综合评级：**PASS — A**

**总评**：这是一次高质量交付。需求底牌的每一条硬约束（标准库、离线 Seam、draft/prerelease 过滤、404/限流路径、token 静默）都有对应代码与测试双重落点；架构上以极薄的接缝换取了整体可测性，`collect_official(fetch_page, limit)` 一处签名隔离了全部网络复杂度，`now` 注入更见功力。开发者对 GitHub API 契约展现了真实的查证行为而非记忆复述（`published_at` vs `created_at` 排序陷阱的处理是最硬的证据）。两处不完美——429 未获 token 提示、ADR 未成文（决策日志代偿）——均为打磨级问题，不构成缺陷。

**移交建议（非阻塞）**：① 给 429 增加与 403 同款的 `GITHUB_TOKEN` 提示并补一例测试；② 有 3.8 环境时复跑一次套件；③ 若项目继续演进，将 `state.json` 的 Q1–Q7 决策沉淀为 `.forge/wiki/decision/` 下的正式 ADR。

---

