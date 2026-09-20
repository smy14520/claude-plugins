"""pytest 根 conftest：

1. 本文件位于项目根，pytest（prepend 导入模式）会将其目录加入 sys.path，
   使 tests/ 下用例可直接 `import storage / domain / todo`；
2. autouse 夹具强制每个用例的 TODO_FILE 指向独立临时文件，
   防止 CLI 用例误写用户主目录的 ~/.todos.json。
"""

import pytest


@pytest.fixture(autouse=True)
def _isolate_todo_file(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))
