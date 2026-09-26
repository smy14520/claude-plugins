# todo-cli

## Goal

`todo` 是装进项目里的本地待办 CLI：在项目目录用纯键盘完成"记一条 → 打标签/定优先级 → 勾掉 → 回看 → 清理"的完整循环，数据是当前目录下的单一 `./.todos.json`——可进 git、可 grep、可手工备份，无服务、无数据库。要解的问题：项目内的待办散落在脑子里和聊天记录里，需要一个跟着项目走、随手可记、可按标签和优先级收窄查看的清单。体验取向 todo.sh 式的极简直给：运行时零依赖（纯 Python 标准库）、纯文本输出可干净进管道、命令面小而语义可预测——过滤即收窄（多标签 AND）、排序让最重要的活浮在主视图顶部。

## Design

### 存储与 schema（接口契约）

- 路径：`./.todos.json`，相对当前工作目录（测试以临时目录为 cwd 隔离）。
- 顶层形状：`{"next_id": <int>, "todos": [<record>...]}`。`next_id` 是持久化的单调计数器：分配一个 id 即 +1、永不回退——rm/clear 删光任务后，新 id 仍不复用任何历史 id（这是"ID 不回收"在空列表下的正确语义）。
- record 字段在 S-001 一次定版，后续 slice 只加 CLI 参数、不改文件格式：
  - `id: int`（自 1 起）、`title: str`（非空）、`tags: [str]`（去重保序）
  - `priority: "high" | "med" | "low"`，add 缺省 `med`
  - `done: bool`、`created_at: str`、`completed_at: str | null`（done=false 时必须为 null）
- 时间戳：UTC ISO 8601（`YYYY-MM-DDTHH:MM:SSZ`）。
- 写入原子性：先写 `<path>.tmp` 再 `os.replace` 原子替换，任何时刻磁盘上要么是旧完整内容、要么是新完整内容。读取时文件缺失视为空列表且**不创建文件**（仅写操作落盘）。

### 状态空间

实体：Task（字段如上）。完成态两值：pending（done=false）/ done（done=true）。

| 从 | 触发 | 到 | 副作用 |
|---|---|---|---|
| —（不存在） | add | pending | 分配 id（消费 next_id）；created_at=now；completed_at=null |
| pending | done | done | completed_at=now |
| done | reopen | pending | completed_at=null；其余字段不动 |
| pending / done | rm | —（删除） | next_id 不回退 |
| done | clear | —（批量删除） | 一次删除全部 done 记录，pending 原样 |
| pending / done | edit | 原态（完成态不变） | 只改显式给出的字段；tags 整体替换语义 |

pending→done 仅经 `done` 命令；done→pending 仅经 `reopen`；`edit` 不改变完成态。无孤悬状态：add 造 pending，done 造 done，reopen 回 pending。

### 命令面（接口契约）

| 命令 | 形式 | 行为要点 |
|---|---|---|
| add | `todo add "标题" [--tag T]... [-p high\|med\|low]` | stdout 报新 id；`--tag` 可重复、逗号分隔等价拆开 |
| list | `todo list [--tag T]... [--priority P] [--all] [--json]` | 默认仅未完成 |
| done / reopen | `todo done <id>` / `todo reopen <id>` | 完成态双向迁移 |
| rm | `todo rm <id>` | 单条删除 |
| edit | `todo edit <id> [--title S] [--tag T]... [-p P]` | 只改给出的字段；`--tag` 语义同 add（可重复、逗号等价拆开）并整体替换 tags；无参 no-op |
| clear | `todo clear` | 批量删除全部已完成 |

### 跨片联动（slice 条目引用本节，不另存副本）

- **过滤叠加**：`--tag`（多标签 AND）、`--priority`、默认"仅未完成"三者取交集；`--all` 只解除"仅未完成"这一条，不影响标签/优先级过滤。空结果是合法结果：文本视图空输出、`--json` 输出 `[]`，两者退出码均为 0。
- **排序唯一规则**（一切 list 视图共用）：未完成按 priority（high>med>low）、同级按 id 升序；`--all` 时已完成整体排在全部未完成之后、按 completed_at 倒序（秒级时间戳同秒时按 id 降序）。排序与过滤参数正交。
- **文本与 JSON 同源**：`--json` 与文本视图走同一份过滤+排序结果，仅渲染不同。stdout 纯净按命令分类：视图命令（list 及其 `--json`）stdout 只输出数据本身；变更类命令在 stdout 报一行确认（`add` 的 stdout 含新 id 由验收条目钉死）。错误与提示一律走 stderr。
- **错误约定**：引用不存在的 id、或状态不满足（对已完成任务 done、对未完成任务 reopen）→ 非零退出 + stderr 说明 + 文件内容不变；用法错误由 argparse 以非零退出处理。

### 工程骨架（接口契约，S-001 建立、其余 slice 消费）

uv 管理的 Python 包，console_script 命令名 `todo`，Python >= 3.12（查证于 2026-09-26，本机 `python3 --version` = 3.12.8），运行时零依赖（argparse/json/os 等纯标准库），dev 依赖仅 pytest，测试命令 `uv run pytest`。模块划分由 impl 定（如 cli / store / model），对外以本节 schema 与命令面为准。

## Acceptance Criteria

通用前提（所有条目默认成立）：测试在临时目录中以该目录为 cwd 运行，数据文件是 cwd 相对路径；条目默认以真实 CLI 行为验证（子进程或等价入口调用），断言落到 `.todos.json` 内容与 stdout/stderr/退出码；存储层内部性质（如原子写）允许单元级测试。

### [x] S-001 最小闭环：add → 持久化 → list（tracer bullet）

* [x] 正向：干净目录 `todo add "买牛奶"` → 退出码 0，stdout 含新 id（#1）；`./.todos.json` 生成且记录字段齐全：id=1、title="买牛奶"、tags=[]、priority="med"、done=false、created_at 为 UTC ISO 8601、completed_at=null
* [x] 正向：同目录新起进程 `todo list` → 输出 #1 行（含 id 与标题）、退出码 0——持久化跨进程成立；再 add 一条得 id=2（自增）
* [x] 正向：`todo --help` → 退出码 0 并展示 add/list 用法（argparse 子命令骨架）；`pyproject.toml` 运行时依赖为空
* [x] 反向：`todo add ""`（空标题）→ 非零退出、stderr 有说明、`.todos.json` 内容不变
* [x] 边界：无 `.todos.json` 的目录 `todo list` → 空输出、退出码 0、且不创建该文件（仅写操作落盘）
* [x] 边界：写入走临时文件 + 原子替换——monkeypatch 使替换步骤抛错时，原 `.todos.json` 内容仍完整且可被 json.load

### [x] S-002 完成与删除的生命周期

* [x] 正向：`todo done 1` → 默认 `list` 不再含 #1、退出码 0；文件中该记录 done=true 且 completed_at 非 null
* [x] 正向：`todo list --all` → 未完成在前、已完成在后并带完成标记；两条 completed_at 不同的已完成任务按完成时间倒序（测试直写文件造数）
* [x] 正向：`todo reopen 1` → #1 回到默认 `list`，completed_at 恢复 null，tags/priority/created_at 与完成前一致
* [x] 正向：`todo rm 2` → `list --all` 不再含 #2；随后 `add` 新任务的 id > 2（不回收）
* [x] 边界：rm/clear 删光全部任务后再 `add` → 新 id 延续持久化计数（next_id），不与本次出现过的任何历史 id 冲突
* [x] 反向：`todo done 99`（不存在 id）→ 非零退出、stderr 有说明、文件内容不变
* [x] 反向：`todo rm 99`（不存在 id）→ 非零退出、stderr 有说明、文件内容不变（删除路径同样不做静默幂等）
* [x] 反向：`todo reopen 1`（#1 尚未完成时）→ 非零退出、文件内容不变；`todo reopen 99`（不存在 id）同理拒绝

### [x] S-003 标签与 AND 过滤

* [x] 正向：在两个隔离目录分别执行 `add "修登录" --tag backend --tag urgent` 与 `add "修登录" --tag backend,urgent`，两记录除 created_at 外逐字段一致（tags=["backend","urgent"]，去重保序）
* [x] 正向：存在 tags={backend} 与 tags={backend,urgent} 两条任务时，`list --tag backend --tag urgent` 只出后者——多标签 AND 收窄
* [x] 正向：`list --tag backend` 每行带出该任务的标签；`list --all --tag backend` 对已完成任务同样过滤（与 --all 叠加）
* [x] 反向：无标签任务不被任何 `--tag` 命中；`list --tag nosuch` → 空输出、退出码 0（空结果不是错误）
* [x] 边界：`--tag "backend,"` 尾随空段被忽略，与 `--tag backend` 完全等价

### [x] S-004 优先级与主视图排序

* [x] 正向：`add -p high` / `add -p low` 记录对应档位；省略 `-p` 落 med
* [x] 正向：混档任务集上默认 `list` 顺序为 high→med→low，两条同级（high）任务按 id 升序
* [x] 正向：`list --priority high` 只出 high；`list --priority high --tag x` 取交集（与 --tag 叠加）
* [x] 正向：`--all` 下已完成项仍整体排在全部未完成之后（completed_at 倒序），未完成段按优先级排序——S-002 的 --all 规则在引入优先级后不回退
* [x] 反向：`add "x" -p urgent`（非法档位）→ argparse 拒绝、非零退出、文件不变
* [x] 边界：全部任务同优先级时顺序退化为 id 升序（排序稳定可预测）

### [x] S-005 维护与脚本化收尾：edit / clear / --json

* [x] 正向：`edit 1 --title "新标题" -p low` 只改标题与优先级，id/tags/created_at/done/completed_at 均不变
* [x] 正向：`edit 1 --tag x --tag y` 将 tags 整体替换为 ["x","y"]，未给 `--tag` 的另一次 edit 不动 tags；对已完成任务 edit 成功且 done/completed_at 不变
* [x] 正向：`clear` 删除全部已完成、未完成项原样保留（含顺序）；无已完成项时 stderr 输出提示、退出码 0、文件内容不变
* [x] 正向：`list --json` 的 stdout 可直接被 json.load（无其他文本混入），输出数组与同参数文本视图同序同集，元素字段与存储记录一致；`--json` 与 `--tag/--priority/--all` 叠加输出对应过滤子集
* [x] 边界：`list --json` 在空结果（含无 `.todos.json` 的目录）时 stdout 恰为 `[]`、可直接被 json.load、退出码 0
* [x] 反向：`edit 99`（不存在 id）→ 非零退出、stderr 有说明、文件不变
* [x] 边界：`edit 1`（无任何修改参数）→ no-op、退出码 0、文件内容不变

## Out of Scope

* Web/GUI 及任何形式的多端同步（用户确认）
* SQLite 及一切数据库——存储只有单文件 JSON（用户确认）
* 截止日期/提醒、循环任务、子任务与依赖（用户确认）
* 关键字搜索（`--grep` 之类）——列表短，标签+优先级过滤够用（用户确认）
* 颜色输出与 TTY 检测——纯文本保证可干净进管道（用户确认）
* `--any`（OR 标签过滤）——留作未来纯增量，不破坏现有语义（用户确认）
* 自定义数据路径 / `TODO_FILE` 环境变量——路径死定 `./.todos.json`（用户确认）
* 多进程文件锁——单用户手动 CLI 不做锁；崩溃安全由原子写入验收条目承担（用户确认）
