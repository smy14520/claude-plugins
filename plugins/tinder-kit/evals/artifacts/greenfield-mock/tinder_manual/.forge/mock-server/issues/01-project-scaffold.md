# 01 项目骨架与打包

Status: resolved
Type: task

## What

`pyproject.toml`（hatchling 后端、`name = "mock-server"`、零 `dependencies`、`[project.scripts]` console script、`[dependency-groups] dev` 仅 pytest、wheel 指向 `src/mock_server`、pytest 配置）；`.python-version` = 3.12；MIT `LICENSE`。

## 验收标准

- [ ] `uv sync` 成功建环境并产出 `uv.lock`
- [ ] `uv run python -c "import mock_server"` 可导入（src layout 生效）
- [ ] `requires-python >= 3.11`，运行时依赖为空

## Comments

- 已完成：`uv sync` 成功（CPython 3.12.8），`uv.lock` 产出，`mock-server==0.1.0` 装入 `.venv`，运行时依赖为空；`import mock_server` 生效。
