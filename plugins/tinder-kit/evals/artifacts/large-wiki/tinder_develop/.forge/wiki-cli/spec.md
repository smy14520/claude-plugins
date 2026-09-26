# Spec: wiki-cli

> 对齐结论源：`.forge/tasks/wiki-cli/state.json`（status: confirmed）· 术语源：`.forge/CONTEXT.md` · 红线：ADR-0001 / ADR-0002

## Problem Statement

个人 Markdown 笔记随时间增长后，链接关系变得不可见：写了 `[[页面]]` 却不知道谁引用了自己；`#tag` 散落在各页无法按主题聚合；"我记得写过这个东西"却找不到在哪页；死链与孤岛页面在不知不觉中积累。现有方案（如 Obsidian）是重型 GUI 应用，不透明、不可脚本化。用户需要一个纯本地、零依赖、可编排进 shell 脚本的命令行工具来回答这些问题。

## Solution

wiki-cli：一个纯标准库 Python CLI。用户指向一个 Vault（Markdown 根目录），通过 5 个子命令获得知识库的结构视图：

- `wiki links [页面]` — 正向出链（省略页面名时给出全 Vault 出链汇总）
- `wiki backlinks <页面>` — 反向引用（"谁链接到我"）
- `wiki tags` — #tag 提取与聚合（计数 + 使用页面）
- `wiki search <关键词...>` — 标题与正文的关键词检索（AND，标题加权）
- `wiki doctor` — 健康体检：死链、孤岛页面、页面名冲突、汇总统计

全部命令支持 `--json`；退出码 0/1/2 供脚本判断。全量扫描 + 内存索引，零数据库、零外部服务（ADR-0002），clone 即用（ADR-0001）。

## User Stories

1. As a Vault 维护者, I want `wiki links <页面>` 列出该页所有出链及其 `文件:行号` 位置, so that 我能看清一页把读者引向了哪里。
2. As a Vault 维护者, I want `wiki links` 省略页面名时输出全 Vault 出链汇总, so that 我能一眼鸟瞰链接结构。
3. As a Vault 维护者, I want `wiki backlinks <页面>` 列出所有指向它的页面, so that 重命名或删除前我知道影响面。
4. As a Vault 维护者, I want `wiki tags` 聚合全部 Tag（计数 + 使用页面清单）, so that 我能按主题导航。
5. As a Vault 维护者, I want 嵌套写法 `#a/b` 作为完整 Tag 字符串聚合, so that 聚合结果可预测、不歧义。
6. As a Vault 维护者, I want 代码块（围栏与行内）内的 `#tag` 与 `[[链接]]` 被忽略, so that 代码示例不污染标签云与链接图。
7. As a Vault 维护者, I want `[[Page|别名]]` 按管道前第一段解析目标, so that 别名链接不产生假 Dead Link。
8. As a Vault 维护者, I want `[[Page#小节]]` 剥离锚点后按页面名解析, so that 小节链接不进 Dead Link 报告。
9. As a Vault 维护者, I want `wiki search 关键词...` 按 Page 名与正文做大小写不敏感子串匹配、多词 AND, so that 我能找回"写过但忘了在哪"的内容。
10. As a Vault 维护者, I want 标题（页面名）命中的 Page 排在正文命中之前, so that 我命名过的页面优先出现。
11. As a Vault 维护者, I want `wiki doctor` 报告每个 Dead Link 的 `文件:行号 + 目标名`, so that 我能逐个修复断链。
12. As a Vault 维护者, I want doctor 报告所有 Orphan, so that 我能把孤岛笔记织回知识网络。
13. As a Vault 维护者, I want doctor 报告 casefold 后同名的 Page 冲突, so that 链接解析的可信度有保障。
14. As a Vault 维护者, I want 链接解析大小写不敏感（casefold）, so that `[[foo]]` 能命中 `Foo.md`。
15. As a 中文文件名的 Vault 维护者, I want NFC/NFD 形态不同的等价文件名与链接互相解析, so that macOS 与其他平台间文件名差异不产生假 Dead Link。
16. As a 中英混排写作者, I want Tag 文法与检索按 Unicode 语义处理（`\\w` 含 CJK）, so that 中文 Tag（如 `#领域驱动设计`）与中英混合 Tag 一等公民。
17. As a Vault 维护者, I want 子目录中的 Page 一并被扫描、`[[子目录/名]]` 精确匹配可选使用, so that 分文件夹的 Vault 完整可用。
18. As a 脚本使用者, I want 每个命令的 `--json` 输出（稳定字段结构）, so that 结果可被程序消费。
19. As a 脚本使用者, I want doctor 退出码区分健康（0）/ 存在问题（1）/ 用法错误（2）, so that 我能用它在 CI 或 shell 脚本里做门禁。
20. As a 新用户, I want 对空目录或无 `.md` 文件的目录执行命令时得到优雅的空结果（不崩溃、不报错栈）, so that 工具可以放心试用。
21. As a Vault 维护者, I want Vault 路径不存在时得到明确的中文错误信息与退出码 2, so that 我能立刻发现路径写错。

## Implementation Decisions

**四子系统职责边界（本 spec 的架构骨架）**

- **Parser** — 单文件解析器：输入 `.md` 文本，输出该页的结构化视图 {页面名, 标题, 出链目标(含行号), Tag 集合, 剥离代码块后的纯文本正文}。职责：围栏代码块（``` 状态机）与行内代码排除；`[[Page|别名]]` 取管道前段；`[[Page#锚点]]` 剥离锚点；Tag 文法（`#` + Unicode 字母/数字/`-`/`_`/`/`，不以数字开头，`#` 前须为行首或非文字字符）。**不知道 Vault 里有哪些页面**——不做任何跨文件判断。
- **LinkGraph** — Vault 级装配器：文件发现（递归，含子目录）、页面名注册表（页面名经 NFC 归一 + casefold 建索引）、出边表。职责：链接目标 → Page 解析（basename 全局匹配为主，`子目录/名` 精确匹配为辅）、唯一性冲突检测（casefold 后同名多文件）、Backlink / Dead Link / Orphan 查询。**依赖 Parser，不依赖 SearchEngine**。
- **SearchEngine** — 检索器：消费 Parser 产出的页面名 + 纯文本正文；大小写不敏感（casefold）子串匹配，多关键词 AND；排序 = 标题命中 > 正文命中，同级按命中次数与页面名稳定排序。**无状态、无持久化**。
- **CLI** — 编排与呈现：argparse 子命令分发、全局 `--json`、退出码策略（0=正常/空结果，1=doctor 发现问题，2=用法错误）、中文人类可读输出。**不含业务规则**，只调用上述三者并格式化。

**页面身份规则**：Page = Vault 内 `.md` 文件，页面名 = 文件名去 `.md` 后缀。链接解析大小写不敏感（casefold）；文件名比较做 Unicode NFC 归一（防 macOS NFD 形态不等价）。casefold 后同名多文件视为冲突，不静默任选。

**红线（用户钉死，见 ADR-0002）**：绝不引入 SQLite / 向量库 / 外部检索服务；索引只存内存；`.wiki_index.json` 仅为未来唯一许可的持久化形态，v1 不实现。

**技术选型（ADR-0001）**：Python ≥ 3.10，零第三方运行时依赖；`src/` 布局，包 `wiki_cli`，pyproject 控制台入口 `wiki`。

**UI 语言**：CLI 帮助与人类可读输出为中文；JSON 字段名为英文（程序消费）。

## Testing Decisions

- **测试框架**：stdlib `unittest`（连测试依赖也为零，与 ADR-0001 精神一致）。
- **Seam 选择**（两个，尽量少且高）：
  1. **CLI 命令层（主 seam）**——端到端：临时目录构造 Vault fixture → 调子命令 → 断言 stdout 内容 + 退出码 + `--json` 结构。LinkGraph / SearchEngine / 退出码 / 中文输出 / 健壮性全部在此层验证。
  2. **Parser 文法层（辅 seam）**——表驱动用例直接喂文本断言解析产物：Tag 字符集矩阵、链接语法矩阵、代码块排除、锚点/别名剥离。
- **好测试的标准**：只断言外部可见行为（输出、退出码、JSON 字段），不断言内部函数调用与私有结构。
- **健壮性验收必须覆盖（写入工单验收标准）**：
  - 中文文件名：fixture 中同时放 NFC 与 NFD 形态的等价名 + 对应 `[[链接]]`，断言解析成功、不报 Dead Link；
  - 中英混合：`#混合tag`、`[[中文页面]]`、中文关键词检索均有用例；
  - 大小写不敏感：`[[FOO]]` ↔ `foo.md` 互解析，且 `Foo.md` + `foo.md` 共存时 doctor 报冲突；
  - 代码块排除：围栏块、行内代码中的 `#tag` / `[[链接]]` 不计入。
- **Prior art**：无（空仓库），本 spec 建立测试基线。

## Out of Scope

- `[[Page#小节]]` 锚点级定位（锚点剥离后按页面名解析，不做小节级 backlink）
- `![[Page]]` 嵌入语法
- jieba 等分词、倒排索引、正则检索模式
- 嵌套 Tag 的层级归并显示（`#a/b` 按完整字符串聚合）
- doctor 豁免名单（首页 / MOC 豁免）
- 持久化索引（`.wiki_index.json` 仅是未来许可边界，v1 不实现）
- 配置文件（Vault 路径一律位置参数，默认当前目录）
- HTML 渲染 / Web / GUI
- Markdown 完整 AST 与渲染

## Further Notes

- 量级假设：个人 Vault 数千文件，全量扫描毫秒~秒级（ADR-0002）；到达数万文件且有延迟感知时重新评估。
- 一切领域命名以 `.forge/CONTEXT.md` 为准：Vault / Page / Link / Backlink / Dead Link / Orphan / Tag / Keyword Search / Health Check；禁用 `_Avoid_` 清单中的同义词。
