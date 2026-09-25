# 02 契约加载与校验

Status: resolved
Type: task

## What

`src/mock_server/contract.py`：`Route` / `Contract` / `ContractError` / `ContractInvalid`（全量收集）、`parse_contract(text)`、`load_contract_file(path)`。校验分支按 spec §1/§3：JSON 语法、顶层类型、缺 `routes`、未知键（顶层/路由/settings）、method 大写合法值、path 以 `/` 开头且无 `?`、status 100~599 拒 bool、headers 值必须字符串。

## 验收标准

- [ ] 合法契约解析为不可变 `Contract`；`body`/`headers`/`settings` 均可缺省
- [ ] 每条错误精确到 `routes[N].field` 或 `settings.<key>`
- [ ] 多处错误一次性全部收集（不 fail-on-first）
- [ ] `tests/test_contract.py` 覆盖上述全部分支

## Comments

- 已完成：`tests/test_contract.py` 27 项全绿（含参数化分支与全量收集断言）。
