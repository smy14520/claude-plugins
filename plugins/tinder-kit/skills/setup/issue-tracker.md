# Issue tracker: Local Markdown

本仓库的需求规格（Spec）、任务与决策工单全部存放在本地 `.forge/` 目录下的纯 Markdown 文件中。

## Conventions

- 每个特性/需求独立成目录：`.forge/<feature-slug>/`
- 主规格（Spec/PRD）位于：`.forge/<feature-slug>/spec.md`
- 拆分的实现工单按文件存放于：`.forge/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始顺序编号（绝不合并在一个大文件中）
- 工单状态以元数据行记录在文件开头（如 `Status: ready-for-agent`）
- 讨论过程与评论追加在文件底部的 `## Comments` 标题下

## When a skill says "publish to the issue tracker"

在 `.forge/<feature-slug>/` 目录下新建对应 Markdown 文件（按需自动创建目录）。

## When a skill says "fetch the relevant ticket"

使用 `Read` 工具读取指定路径的文件（用户通常会直接传入文件路径或编号）。

## Wayfinding operations

由 `/wayfinder` 使用。**地图（Map）**是一个主文件，每个决策票是其同目录下的子文件。

- **地图（Map）**: `.forge/<effort>/map.md` — 承载 Notes / Decisions-so-far / Fog 正文。
- **子决策票**: `.forge/<effort>/issues/NN-<slug>.md`，从 `01` 开始顺序编号，文件开头包含 `Type:` 行（`research`/`prototype`/`grilling`/`task`）与 `Status:` 行（`claimed`/`resolved`/`needs-triage`）。
- **阻塞依赖（Blocking）**: 文件顶部注明 `Blocked by: NN, NN`。当所列依赖文件的状态全为 `resolved` 时，该决策票即视为解除阻塞。
- **Frontier 查询**: 扫描 `.forge/<effort>/issues/` 目录下所有处于未解决、未阻塞且未被认领的文件；按编号最小者优先开工。
- **认领（Claim）**: 在动手前使用 `Edit` 工具将该文件的状态更新为 `Status: claimed` 并保存。
- **结案（Resolve）**: 在文件末尾追加 `## Answer` 章节记录结论，将状态更新为 `Status: resolved`，随后将决策指针（核心摘要与链接）追加至 `map.md` 的 `Decisions-so-far`。
