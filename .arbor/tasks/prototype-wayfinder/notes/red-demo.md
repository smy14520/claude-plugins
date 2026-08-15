# 红灯演示：目录对账测试可红（S-004）

对账测试上线前，人为制造两种登记失真，确认测试真实变红（非恒真断言）。演示后已恢复，全套 pytest 跑绿。

- 日期：2026-08-15
- 测试文件：`plugins/seed-kit/tests/test_prompt_contract.py`
- 被测对账源：`plugins/seed-kit/skills/references/conventions.md` ↔ 磁盘 `skills/*/`（含 SKILL.md 的目录）、`agents/*.md`、`commands/*.md`

## 形态一：登记表删去条目（PRD 条文指定形态）

注入（`skills/references/conventions.md` Skill 登记行）：

```diff
- `seed-kit:research` / `seed-kit:wayfinder` / `seed-kit:wiki`
+ `seed-kit:research` / `seed-kit:wiki`
```

命令与结果：

```console
$ python3 -m pytest tests/test_prompt_contract.py::SeedPromptContractTests::test_directory_ledger_reconciles_with_disk -q
AssertionError: 'seed-kit:wayfinder' not found in '# seed-kit 通用约定…'
FAILED tests/test_prompt_contract.py::SeedPromptContractTests::test_directory_ledger_reconciles_with_disk
1 failed
```

失败点：`test_directory_ledger_reconciles_with_disk` 的磁盘→登记方向断言——磁盘上 `skills/wayfinder/` 存在而登记表漏登，测试红。

## 形态二：列举与数量词失真（漏更新数量声明的常见形态）

注入（conventions.md 原则区数量声明，登记行未动）：

```diff
- 十个 skill（research、brainstorm、wayfinder、impl、impl-agent、check、review、wiki、init、handoff）
+ 九个 skill（research、brainstorm、impl、impl-agent、check、review、wiki、init、handoff）
```

命令与结果：

```console
$ python3 -m pytest tests/test_prompt_contract.py -q
FAILED tests/test_prompt_contract.py::SeedPromptContractTests::test_skill_count_ledgers_match_disk
1 failed, 30 passed
```

失败点：`test_skill_count_ledgers_match_disk` 的列举对账——`conventions 列举 [...] ≠ 磁盘 [... 'wayfinder' ...]`，测试红。

## 恢复与收尾

两种注入均从备份恢复（`git diff plugins/seed-kit/skills/references/conventions.md` 复核无残留注入），随后：

```console
$ cd plugins/seed-kit && python3 -m pytest tests/ -q
138 passed
```
