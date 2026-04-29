# 反模式

`.wiki/` 是项目本地 orientation/index layer。它帮助 AI/人类快速定位上下文，但不替代代码、`.arbor` 或外部来源。

---

## AP1 — 把 wiki 当 source of truth

不要根据 wiki 直接改代码或下 review 结论。wiki 可以提示要读哪些文件、symbol、contract、测试；真正实施前必须验证当前代码和 `.arbor`。

正确做法：`wiki-collect` → 读取相关页面 → 验证代码/`.arbor` → 决策。

---

## AP2 — 向量检索 / embedding 检索

不要为 `.wiki` 构建向量库。sdd-kit 的检索入口是 deterministic helper：

```text
sdd-arbor wiki-index --json
sdd-arbor wiki-search "<query>" --json
sdd-arbor wiki-collect --query "<query>" --limit 5 --json
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

## AP7 — task.md 依赖 wikilinks

`task.md` 必须自包含。可以在 PRD 里链接 wiki 作为背景提示，但执行计划不能要求实现者跟随 wikilink 才知道要做什么。

---

## AP8 — 隐式技能串联

Wiki skill 不自动调用 research/brainstorm/task/impl/review；其他 skill 也不静默写 wiki。需要写入时由用户显式要求，或在 package 达到稳定 milestone 后显式请求 module summary publish。

---

## AP9 — 缺少 description / summary

没有 `description` 的页面会降低 `wiki-index/search/collect` 的可用性。新页面至少写 `title`、`description`、`tags`、`type`、`summary`。

---

## AP10 — 把 `.wiki` 写回 `.arbor/wiki`

默认 wiki root 是项目内 `.wiki/`。除非用户显式覆盖 `--wiki-root .arbor/wiki`，不要把 wiki 写入 `.arbor/wiki`。