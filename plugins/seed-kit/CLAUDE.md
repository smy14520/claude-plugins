# seed-kit

## 核心原则：机制在插件，标准在项目

**插件提供开发机制**：交付承诺、验证手段、覆盖校验、通过门槛、迭代循环、工具链。

**项目定义自己的标准**：UI 规范、架构原则、设计语言、质量基线、参考范例。写在项目 `CLAUDE.md` / `DESIGN.md` / `.claude/rules/`，harness 自动加载。

为什么不混在一起：换项目不改插件——标准随项目长，机制不动。插件不硬编码任何项目的 UI 规范、架构偏好、质量门槛。项目缺标准时，插件只提供防半成品的底线纪律，之上由对抗性评审把关。

**判定式**：一行内容能否留在插件，取决于它是否对所有技术栈同等成立——若它对 Web 成立但对纯 CLI、游戏引擎、嵌入式不成立，它是项目标准，应移到项目。正例（栈无关，可留）：三类验证 kind、验收条目驱动、review loop 控制流。反例（栈相关，应移）：Playwright/computed-style/a11y/Pact/Unity/Unreal 等具体工具名、按技术栈分类的测试方法清单、截图/浏览器/页面等特定产物形态假设。

## 验证哲学：gate 守硬事实，loop 守好坏

**硬事实**（正确性）用通过门槛：一次判定、不可妥协——项目测试全过、质量命令全绿、产物存在。

**好坏**（体验/完整性/充分性）用迭代循环：逼近、无硬终点——评审发现问题 → 修复 → 再评审，直到无新发现。

把好坏塞进门槛会异化为凑阈值（执行者优化通过而非体验）。评审是循环的质量信号，不是门槛；完成是循环收敛的结果，不是"过门槛"。

感知型判断（完整性、割裂感、充分性）没有机械规则，归属独立语义评审，不是机制。

**验收条目必须过，PRD 中描述的方向是期望——用判断力逼近它，不进 gate。**

## 边界

- 验证是整体判断，不做逐条 obligation 合规
- 插件不内置技术栈特定的测试方法清单——测试工具由项目配置声明
- 体验质量走 review loop，不用 scoring gate 卡 done
- skill 进入要么用户发起，要么 agent 提议后用户同意，绝不单方进入——例外：PRD 定稿后 brainstorm 自动派 seed-prd-review（默认收尾工序）；重操作（impl 开工、review-loop、architect）须显式点名
- agent 不自动 commit——PRD checkbox 记进度，done-log 记机械验证，review-loop marker 记显式终态；提交由用户决定

## 行为评估（seed-kit-evals-v2）

测本插件是否真正塑造 Coding-Agent 行为时，用独立仓库 **seed-kit-evals-v2**，不要在本目录里发明第二套 benchmark 流程。

**每次要出题、跑测试用例、做效果对比之前，先读本目录 [`EVALS.md`](EVALS.md)（快速上手）与 evals-v2 仓库的 `EVALS.md`（完整手册）**——场景合同以 `seed-evals check` 为准。

- 默认路径：`/Users/camellia/Personal/Code/claude/seed-kit-evals-v2`；改 skill 时 cwd=本目录，跑评测时用 `/Users/camellia/Personal/Code/claude/seed-kit-evals-v2/bin/seed-evals`（任意 cwd 可用）
- 套件方向：全流程旅程 + 效果对比实验 + 极少量 infra 冒烟；不做每触发点微点覆盖，活跃资产见 `scenarios/MANIFEST.md`
- 环境与默认值在 `config/local.json`；`seed-evals doctor` 自检，`sentinel` 日常回归，`value <exp>` 跑对比实验
- 失败先归因（infra / 场景质量 / 插件行为 / harness），再决定改插件还是改场景；infra 类 indeterminate 会自动重试并入 `seed-evals stability` 统计
- 旧版 v1 实验室与 [`EVALS_V1.md`](EVALS_V1.md) 是历史资料（2026-07-18 前）；改 prompt 前先翻 evals-v2 各实验的 CONCLUSION.md，别重复已被证伪的方向
