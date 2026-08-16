# 设计：统一 impl + 任务档案（dossier）

## 1. 依据（数据，不是感觉）

`seed-kit-evals-v2/experiments/impl-vs-impl-agent-value/CONCLUSION.md`（2026-07-25 跑，07-26 用户拍板）：

- 完成率 treatment +2.2pp（复评 +1.8pp）——**接近噪音**；
- token 8.55M vs 1.65M（+419%）、耗时 ~2x、成本 $9.14 vs $1.23（+645%）——**结构性**（per-slice 派发 + per-slice review + 集成 review 的轮次开销）；
- 当时的结论是"impl-agent 可选不默认"。本任务走完最后一步：删除。同时保留它唯一被承认的特性——**中断可续接**（盘上事实驱动），补上它自己承认的弱点——"handoff 在内存、中断会丢"。

## 2. 删 / 改 / 留总览

| 资产 | 处置 | 理由 |
|---|---|---|
| `skills/impl-agent/` | **删** | 成本结构性、增益≈噪音 |
| `agents/seed-slice.md` | **删** | 唯一调用方是 impl-agent，孤儿化 |
| `seed next-action` | **删**（吸收进 status） | 单一线性流程下与 status 信息重复 |
| `seed impl-state show` | **删**（并入 status） | 三个读面归一为单一投影面 |
| `seed impl-state init` | **留** | 锚点初始化，dossier 创建入口 |
| `seed impl-state reset-attempts` | **留** | 熔断清零语义不变 |
| `seed handoff add` | **新增** | handoff 落盘的窄写入口 |
| `seed done --evidence-*` | **扩展** | 验证时刻顺手落证据指针 |
| `seed status` | **扩展** | + 锚点 / handoff·evidence 存在性 / gate 失败计数 |
| `agents/seed-impl.md` | **扩展** | 返回结构加 `handoffs` |
| done-log / gate-attempts / checkbox | **不动** | 机器真相层，`seed done` 独占写 |

## 3. dossier schema（impl-state.json）

```json
{
  "task_start_sha": "a1b2c3d",
  "git_root": "/path/to/repo",
  "prd_sha256": "…",
  "created_at": "2026-08-16T…",
  "slices": {
    "S-001": {
      "handoff": ["create_order() 返回 {id, status:'pending'}，回调必须查 pending 才放行"],
      "evidence": {
        "files": [".arbor/tasks/<task>/evidence/S-001-01-stroke-drawn.png"],
        "artifact": {"url": "http://localhost:5173", "mode": "dev"},
        "commit": null
      }
    }
  }
}
```

| 字段 | 写者 | 时机 | 性质 |
|---|---|---|---|
| task_start_sha / git_root / created_at | `impl-state init` | 入场一次 | **lock-once**，re-init 不覆盖 |
| prd_sha256 | `impl-state init` | 入场 + re-init | 漂移检测（checkbox 翻转归一化） |
| slices.*.handoff | `seed handoff add` | agent 返回后 / 中断前 | append-only 列表 |
| slices.*.evidence | `seed done --evidence-*` | gate 通过时 | 与 done-log 同批写入 |

**不变量**（腐化防护）：
1. 进度权威 = PRD checkbox；dossier 不构成第二进度（status 只呈现存在性，不呈现"完成"语义）。
2. 验证事实（命令、exit code）只在 done-log；dossier 只存**指针**（文件路径 / URL / commit）。
3. dossier 全部由 CLI 窄命令写入，模型不手编 JSON；结构由 pytest 合同守护。
4. seed-assert / review 消费 evidence 时**核验指针**（文件存在、commit 匹配），不信指针本身。
5. 写序：done-log → dossier → checkbox。中断最坏态是"有证据未勾选"（重跑 `seed done` 补齐），永不出"已勾选无证据"。

## 4. 统一后的 impl 流程

```
入场：seed impl-state init（锚点 + 建 dossier）
  → 读 seed status（checkbox + handoff + evidence + gate 计数）续接或开新
  → 派 seed-impl（全量或剩余 slice，单 agent）
  → agent 返回：逐 slice seed handoff add（隐性事实落盘）
  → 逐 slice seed done --test … --evidence…（gate + 证据）
  → 收尾自查（现状不变）→ review-mark
接手方（新终端）：读 impl-state.json + seed status 即得全量上下文
```

**已知限制（如实声明）**：handoff 的落盘粒度 = **派发边界**。agent 运行中被 kill，当次运行的隐性上下文仍会丢（与现状一致）；checkbox + done-log + 工作区代码仍是兜底。takeover eval（S-005）度量这个 gap 是否值得进一步补（例如分批派发），数据说话再动。

## 5. eval 设计（S-005）

- **场景** `impl-takeover-resume`：fixture 建 5-slice 任务，先驱动完成 S-001/S-002（treatment 臂在此期间执行 `seed handoff add` 落盘 planted 隐性依赖；control 臂不写），然后**新会话**接管做 S-003+。
- **planted gap**：S-002 的实现里埋一个代码可见但语义不可见的接口决策（如状态字段返回 `'pending'` 而非直觉的 `'created'`，且 S-003 的支付回调依赖它）；该事实只存在于 handoff。control 臂只能从代码反推——planted 让反推可错。
- **判据**：接管会话 token 成本、首个正确动作延迟、S-003 是否踩坑（planted 依赖错误 = fail）。
- **类型**：value_ab，treatment=dossier / control=现状，各 ≥2 trials；control 不删插件本体（只不执行 handoff 写入）。
- 复用既有 harness：journey 形态，checks 断言产物正确性，不断言"调用了 handoff"。

## 6. Alternatives considered（它打败了什么）

1. **双流程并存（impl-agent 可选）**——被 impl-vs-impl-agent-value 证伪：增益≈噪音、成本 +419%/+645% 结构性；且双流程带来持续维护税（skill 双份减肥、eval 双套资产、文档双叙述）。
2. **证据进 done-log 而非 dossier**——单写者优雅，但 takeover 需拼读多文件；被"接手方读一个文件拿到锚点+交接+证据"取代。done-log 回归纯机器验证流水。
3. **模型手编 dossier JSON**——被窄 CLI 写入取代：结构可测、原子性可控、幻觉写坏不波及进度（不变量 3）。
4. **保留 next-action 独立命令**——被 status 吸收：其独有产出（gate 失败计数、熔断推导）成为 status 的派生字段，少一个命令面。

## 7. 风险

- **删错方向风险**：若未来任务普遍 slice 巨多且分层数据显示"slice 越多 per-slice 隔离增益越大"（原实验未判定），单流程可能重新吃亏。对策：本任务 CONCLUSION 记录复活条件；impl-vs-impl-agent-value 的复跑入口保留在 evals 仓库。
- **dossier 膨胀风险**：handoff 无节制累积会让档案变成噪音。对策：`seed handoff add` 保持"代码与 git 读不出的隐性事实"边界（agent prompt 已有该纪律）；status 只显示存在性不倾倒内容。
- **takeover eval 的 planted gap 造得太容易/太难**：对照既有 planted-gap 场景（cross-plugin 系列）的埋法，先 check-red。
