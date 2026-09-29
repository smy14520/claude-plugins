"""vault 定位与用法错误（checklist 4）：--vault 覆盖、默认 CWD、错误 exit 2。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path

BASIC_HOME_OUTPUT = (
    "home.md (home)\n"
    "→ python.md  [[python]]\n"
    "→ python.md  [[python|Py 学习笔记]]\n"
)


def test_vault_defaults_to_current_directory(monkeypatch) -> None:
    monkeypatch.chdir(vault_path("links-basic"))
    code, out, err = run_cli(["links", "home"])

    assert code == 0
    assert out == BASIC_HOME_OUTPUT


def test_vault_flag_overrides_working_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # 当前目录不是 vault
    code, out, err = run_cli(["--vault", str(vault_path("links-basic")), "links", "home"])

    assert code == 0
    assert out == BASIC_HOME_OUTPUT


def test_missing_vault_path_exits_2_with_usage_hint() -> None:
    code, out, err = run_cli(["--vault", "/nonexistent/vault/path", "links", "home"])

    assert code == 2
    assert "usage:" in err
    assert "vault 不存在" in err
    assert "/nonexistent/vault/path" in err


def test_vault_path_to_a_file_exits_2(tmp_path) -> None:
    not_a_dir = tmp_path / "plain-file.md"
    not_a_dir.write_text("不是目录", encoding="utf-8")
    code, out, err = run_cli(["--vault", str(not_a_dir), "links", "home"])

    assert code == 2
    assert "usage:" in err
    assert "不是目录" in err


def test_links_without_page_argument_exits_2() -> None:
    code, out, err = run_cli(["links"])

    assert code == 2
    assert "usage:" in err


def test_unknown_page_exits_2_with_clear_message() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("links-basic")), "links", "no-such-page"])

    assert code == 2
    assert "no-such-page" in err
    assert out == ""
