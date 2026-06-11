# 反模式

`.wiki/` 是项目本地 orientation/index layer。它帮助 AI/人类快速定位上下文，但不替代代码、`.arbor` 或外部来源。

---

## AP1 — 把 wiki 当 source of truth

不要根据 wiki 直接改代码或下 review 结论。wiki 可以提示要读哪些文件、symbol、contract、测试；真正实施前必须验证当前代码和 `.arbor`。

正确做法：`sdd-wiki collect` → 读取相关页面 → 验证代码/`.arbor` → 决策。

---

## AP2 — 向量检索 / embedding 检索

不要为 `.wiki` 构建向量库。sdd-kit 的检索入口是 deterministic helper：

```text
sdd-wiki index --json
sdd-wiki search "<query>" --json
sdd-wiki collect --query "<query>" --limit 5 --json
```

原因：frontmatter、tags、summary、wikilinks、locators 已经提供可解释检索路径；embedding 会引入不可解释噪声和额外维护成本。

---

## AP3 — 自动摄入所有变更

不要在每次代码修改、每次 impl/review 后自动写 wiki。自动摄入会把临时状态和噪声写成长期知识。

正确触发：用户显式要求 ingest，或 package 到达稳定 milestone 后由 lead 请求 module summary publish。

---

## AP4 — index.md 变成全量目录

`index.md` 只做入口，不复制每个 root 的所有子页面。重复导航会腐化。

正确做法：root 页面承载领域导航；retrieval helper 扫描 nested `.wiki/**/*.md`。

---

## AP5 — 机械式代码转录

不要把单个文件里已有的方法列表、schema 字段、API 列表完整复制进 wiki。

正确做法：记录跨文件才能重建的信息、不可见约束、稳定 contract、关键 locator 和验证线索。

---

## AP6 — Module note 写行号

不要写 `foo.py:123` 作为 module locator。行号会随重构快速失效。

正确 locator：file path + class/function/method、route name、table/index、config key、test name、contract id。

---

## AP7a — 把核心 scope 外包到 wiki

不要把 PRD 的 goal、scope、Acceptance Criteria 等核心需求藏在 wiki 里。即使 wiki 全部缺失，impl 看 PRD 也必须知道做什么。

- ❌ PRD 写“按 [[新增导出]] 实现全部内容” —— 核心 scope 完全外包。
- ✅ PRD 写“在 auth 模块新增导出函数 X，签名见下，涉及全项目多处同步修改；同步位置详见 [[新增导出]]” —— 核心 scope 在 PRD，wiki 仅作辅助。

## AP7b — cross-cut 页面可以引用，但需要 fallback

PRD 可以引用 wiki cross-cut 页面（如 `新增导出`、`API 路由注册`、`新增 enum 值`、`数据库迁移` 等）作为防漏辅助，但引用必须满足：

- 核心 scope（做什么、为什么、验收）在 PRD 自包含。
- wikilink 仅承担"防漏点"职责，不承担"做什么"职责。
- PRD 写明 fallback：清单缺失或与现状不一致时 impl 调研代码逐一识别。
- brainstorm 写引用前先 `sdd-wiki collect --query "<keyword>"`，只引用结果中实际存在的 page title/path，不要凭记忆写 wikilink。

PRD 引用 wiki 的标准三层结构见 `page-types.md` "PRD 引用 wiki 的范式"。

---

## AP8 — 隐式技能串联

Wiki skill 不自动调用 research/brainstorm/impl/review；其他 skill 也不静默写 wiki。需要写入时由用户显式要求，或在 package 达到稳定 milestone 后显式请求 module summary publish。

---

## AP9 — 缺少 description / summary

没有 `description` 的页面会降低 `sdd-wiki index/search/collect` 的可用性。新页面至少写 `title`、`description`、`tags`、`type`、`summary`。

---

## AP10 — 把 `.wiki` 写回 `.arbor/wiki`

默认 wiki root 是项目内 `.wiki/`。除非用户显式覆盖 `--wiki-root .arbor/wiki`，不要把 wiki 写入 `.arbor/wiki`。

---

## AP11 — 重复维护 single-source

不要在两个 page 都写完整的相同内容。每个内容片段只在一个 page 权威定义，另一个 page 用 wikilink + 一行 anchor 引用。

- ❌ `Modules/auth.md` 和 `新增导出.md` 各自都列出 auth 的全部导出函数清单 —— 改一处忘改另一处必然腐化。
- ✅ `Modules/auth.md` 是 auth 内部细节的 single source（包含函数签名）；`新增导出.md` 在自己视角写“auth 同步修改位置 + 命名规则，详细函数清单见 [[Modules/auth]] § 对外契约”。

判断方法：

- 内容**只对单个模块成立** → single source 在该 module page。
- 内容**跨模块才有意义**（命名映射、规则比较、跨域联动） → single source 在 cross-cut page。
- 两边都不复制完整内容，只 anchor。

`sdd-wiki lint` 的 `broken_wikilink` error 只检测目标页面是否存在，不检测 section anchor。被引用 section 的标题需要人工保持稳定；重命名前先 `grep -r "[[页面名]]"` 找出所有引用点同步更新。