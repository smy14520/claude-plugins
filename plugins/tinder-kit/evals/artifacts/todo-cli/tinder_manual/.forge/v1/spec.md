# Spec: tdo v1 — 本地 CLI Todo

- Status: ready-for-agent
- 来源：/grill-with-docs 访谈（2026-09-25），全部决议经用户逐项确认
- 术语：见 `.forge/CONTEXT.md`；存储决策：见 `.forge/wiki/decision/0001-single-json-file-storage.md`

## 目标

单用户本地 CLI 待办工具：标签过滤 + 本地单 JSON 文件持久化。运行时零第三方依赖（纯标准库）。

## 领域规则

- Task 字段：title（strip 后非空，允许重复）、tags（小写归一/去重/排序）、
  status（pending | done）、created_at / completed_at（ISO-8601 UTC，秒级，`Z` 后缀）
- Tag：唯一组织维度；无独立注册表，由 Task 派生；
  `tdo tags` 按 count 降序（同数按名升序）
- 状态迁移：`done` 与 `reopen` 均幂等；`rm` 为硬删（`.bak` 轮转兜底），无确认提示
- 过滤：每个 `--tag` 出现 = 一个 OR 组；组间 AND；无排除语法；
  未知标签（无任何任务使用）→ 空结果 + stderr 提示，退出码 0
- ID：文件内递增，由持久化高水位 `next_id` 计数器分配，删除后永不复用
  （实现注记：访谈时的 `max + 1` 方案在删除最大 ID 任务后会复用 ID，被测试实证推翻，
  故在 D3 schema 顶层增补 `next_id` 字段——永不复用语义优先于原机制描述）

## 命令面

可执行名 `tdo`（`todo` 已被本机 `/opt/anaconda3/bin/todo` 占用）。

| 命令 | 行为 |
| :--- | :--- |
| `tdo add TITLE [--tag TAG]...` | 录入 pending 任务；`--tag` 可重复，逗号拆多标签；空标题 → exit 2 |
| `tdo ls [--tag TAG]... [--all] [--json]` | 默认 pending，ID 升序；行格式 `[ ] 3 买牛奶 #shopping`，`[x]` 为 done；ID 宽度自适应右对齐 |
| `tdo done ID` | pending → done，写 completed_at；对 done 任务 no-op 提示、exit 0 |
| `tdo reopen ID` | done → pending，清 completed_at；对 pending 任务 no-op 提示、exit 0 |
| `tdo rm ID` | 硬删；未知 ID → stderr、exit 1 |
| `tdo tags [--json]` | 标签清单 `tag (count)`，count 降序 |

`--json` 仅 `ls` / `tags` 支持；变更类命令输出人类文本（如 `Added #3 …`）。

## 存储与工程约束

- 单 JSON 文件 `~/.todo/todo.json`，顶层 `{"version": 1, "next_id": N, "tasks": [...]}`；
  `TODO_HOME` 环境变量覆盖目录；temp + rename 原子写；写盘前旧文件轮转 `.bak`
- 文件损坏 / 形状异常 / 版本不识别 → 拒绝读取，提示从 `.bak` 恢复，exit 1
- pyproject 标准包（hatchling 构建），`requires-python >= 3.10`，版本 0.1.0；
  `uv tool install .` 安装；pytest 为 dev-only 依赖
- 退出码：0 成功；1 运行错误（未知 ID、存储损坏）；2 参数/校验错误（argparse 与空标题）
- 测试覆盖：存储 roundtrip（含 `.bak` 轮转、`TODO_HOME`、损坏检测）、
  过滤逻辑（AND/OR、pending 默认、未知组）、ID 分配（不复用）、CLI 退出码
