# cli-todo

本地 CLI Todo 工具：Tag 过滤 + 本地持久化，**零第三方依赖**（纯 Python 标准库）。

## 运行

无需安装，在仓库根目录直接：

```bash
python -m todo <命令> ...
```

或可选安装获得 `todo` 命令：

```bash
pip install -e .
todo <命令> ...
```

## 命令

| 命令 | 说明 |
| :-- | :-- |
| `todo add "标题" [--tags a,b] [--priority high\|med\|low]` | 添加 Todo；可挂多个 Tag，三档优先级（默认 med） |
| `todo list [--tag T ...] [--all]` | 列出未完成（`--all` 含已完成）；`--tag` 可重复，**AND 交集**语义 |
| `todo done <id>` | 标记完成 |
| `todo undo <id>` | 翻回未完成 |
| `todo rm <id>` | 删除 |
| `todo tags` | 列出所有在用的 Tag |

## 示例

```bash
$ python -m todo add "买牛奶" --tags 生活,采购 --priority high
已添加 Todo 1：买牛奶
$ python -m todo add "写周报" --tags 工作
已添加 Todo 2：写周报
$ python -m todo list --tag 工作 --tag 紧急   # AND 过滤
$ python -m todo list
[2] [med] 写周报  #工作
$ python -m todo done 2 && python -m todo list --all
[1] [high] 买牛奶  #生活 #采购
[2] ✓ [med] 写周报  #工作
$ python -m todo tags
工作 生活 采购
```

## 存储

- 数据落盘在当前目录的单一 JSON 文件 `.todos.json`，人可直接查看、手改救急（决策记录见 `.forge/wiki/decision/0001-single-json-file-storage.md`）；
- 环境变量 `TODO_FILE` 可覆盖存储路径（用于测试隔离或多份清单），不会产生第二个数据文件；
- 写入经临时文件 + 原子替换，不留半写状态。

## 开发

```bash
python -m pytest          # 全量测试
python -m mypy todo       # 类型检查
```

术语表见 `.forge/CONTEXT.md`（Todo / Tag / Priority）。
