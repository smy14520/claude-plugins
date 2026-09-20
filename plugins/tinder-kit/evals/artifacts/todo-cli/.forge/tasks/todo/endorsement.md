# Endorsement — todo（独立双轴审查）

- 审查者：只读独立 Reviewer（review skill 程序）
- 日期：2026-09-20
- 审查对象（绿地全新全集，无 git）：`todo.py`、`storage.py`、`domain.py`、`conftest.py`、`tests/test_storage.py`、`tests/test_domain.py`、`tests/test_cli.py`
- 契约锚点：`.forge/tasks/todo/spec.md`（三条 Agreed Seams）；交接：`.forge/tasks/todo/handoffs/03-impl.md`

## 一、Spec 轴（契约兑现度）：PASS / VERIFIED

### Seam 1 存储层往返契约 — 兑现
- 接口存在且精炼：`storage.load(path)`（storage.py:16）/ `storage.save(path, todos)`（storage.py:25），深模块合格：临时文件、fsync、rename、编码全部藏在内部，调用方零感知。
- 往返无损（id/text/tags/priority/done/created_at 全字段）：tests/test_storage.py:16-37 逐字段断言。
- 缺省空表：storage.py:19 `not file.exists() → []`；tests/test_storage.py:12。
- 原子写：storage.py:31-47 —— `mkstemp(dir=target.parent)`（同目录=同文件系统）+ `os.fdopen` + `flush` + `fsync` + `os.replace`；`except BaseException` 清理临时文件后 re-raise（比 `except Exception` 更完备，覆盖 KeyboardInterrupt）。行为侧证据：tests/test_storage.py:65-73 断言目录无 `.tmp` 残留。
- UTF-8 原字符：storage.py:37 `ensure_ascii=False`；tests/test_storage.py:52-55 字节级 `raw.decode("utf-8")` 后断言 `"买牛奶" in decoded`（能抓出 `\\uXXXX` 转义的偷懒实现）。独立烟测复核：落盘文件 `cat` 可直接见中文原字符，JSON 数组形态。
- 绝不使用数据库：全项目 import 仅 argparse/json/os/sys/tempfile/pathlib/datetime，无任何 DB 痕迹。

### Seam 2 领域逻辑契约 — 兑现
- 标签解析：domain.py:17-30 —— `+token` 且非裸 `+` 一律收为标签（含未预定义），去重排序；裸 `+` 与文内 `1+1` 留正文（tests/test_domain.py:29-37）。
- 三档优先级：domain.py:12 `PRIORITIES` 单一事实来源；CLI 侧 argparse `choices=domain.PRIORITIES`（todo.py:108）；独立烟测 `--priority urgent` → rc=2 + stderr。领域守卫 `validate_priority`（domain.py:33-38）有独立参数化测试（含 None/1/大小写变体）。
- 交集过滤：domain.py:76-78 `_has_all_tags` 全包含语义；tests/test_domain.py:75-82（x∧y → 仅 id2）。
- done 显隐：domain.py:68-72 默认藏、`show_done` 显；CLI `--all` 接线正确（todo.py:53）。
- 排序：domain.py:81-83 `(priority_rank, id)`，rank 由 PRIORITIES 推导；tests/test_domain.py:96-105 断言 `[2,4,3,5,1]` 精确序。
- id 稳定性（A9）：domain.py:43 `max+1` 起始 1；rm 最大 id 后复用次大+1 有专门用例（tests/test_cli.py:55-63）。

### Seam 3 CLI 端到端契约 — 兑现
- 五命令 add/list/done/rm/tags 齐备（todo.py:98-137），`main(argv) -> int` 永不抛 SystemExit（todo.py
