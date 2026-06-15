from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))

import seed_guard  # noqa: E402


def edit_payload(path: str, old: str, new: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": old, "new_string": new}}


def test_blocks_checkbox_flip_via_edit():
    result = seed_guard.evaluate(
        edit_payload("/repo/.arbor/tasks/demo/prd.md", "### [ ] S-001 步骤", "### [x] S-001 步骤")
    )
    assert result["decision"] == "block"
    assert "seed done" in result["reason"]


def test_allows_normal_prd_edit():
    result = seed_guard.evaluate(
        edit_payload("/repo/.arbor/tasks/demo/prd.md", "## 背景与目标", "## 背景与目标\n\n补充一句")
    )
    assert result["decision"] == "allow"


def test_allows_unflipping_checkbox():
    # [x] → [ ]（回退）不增加勾选数，不拦截
    result = seed_guard.evaluate(
        edit_payload("/repo/.arbor/tasks/demo/prd.md", "### [x] S-001 步骤", "### [ ] S-001 步骤")
    )
    assert result["decision"] == "allow"


def test_blocks_checkbox_increase_via_write(tmp_path: Path):
    prd = tmp_path / ".arbor" / "tasks" / "demo" / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("### [ ] S-001 步骤\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(prd), "content": "### [x] S-001 步骤\n"}}
    assert seed_guard.evaluate(payload)["decision"] == "block"


def test_allows_write_preserving_checked_count(tmp_path: Path):
    prd = tmp_path / ".arbor" / "tasks" / "demo" / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("### [x] S-001 步骤\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(prd), "content": "### [x] S-001 步骤\n\n补充说明\n"}}
    assert seed_guard.evaluate(payload)["decision"] == "allow"


def test_blocks_manual_evidence_write():
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "/repo/.arbor/tasks/demo/evidence/S-001/001-automated.json", "content": "{}"},
    }
    result = seed_guard.evaluate(payload)
    assert result["decision"] == "block"
    assert "run-check" in result["reason"]


def test_blocks_evidence_shell_redirect():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo '{}' > .arbor/tasks/demo/evidence/S-001/fake.json"},
    }
    assert seed_guard.evaluate(payload)["decision"] == "block"


def test_blocks_destructive_commands():
    for command in ["rm -rf build", "git reset --hard HEAD~1", "git push --force origin main"]:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        assert seed_guard.evaluate(payload)["decision"] == "block", command


def test_allows_normal_bash():
    payload = {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest tests/ -q"}}
    assert seed_guard.evaluate(payload)["decision"] == "allow"


def test_allows_edit_outside_seed():
    result = seed_guard.evaluate(edit_payload("/repo/src/app.py", "- [ ] todo", "- [x] todo"))
    assert result["decision"] == "allow"
