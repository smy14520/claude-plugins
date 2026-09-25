import json

from tdo import cli


def run(monkeypatch, capsys, tmp_path, *argv):
    monkeypatch.setenv("TODO_HOME", str(tmp_path))
    code = cli.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_full_flow(monkeypatch, capsys, tmp_path):
    code, out, _ = run(monkeypatch, capsys, tmp_path, "add", "买牛奶", "--tag", "Shopping")
    assert (code, "Added #1 买牛奶" in out) == (0, True)

    code, out, _ = run(monkeypatch, capsys, tmp_path, "add", "交报告", "--tag", "work,urgent")
    assert "Added #2" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "ls")
    assert "[ ] 1 买牛奶 #shopping" in out
    assert "交报告" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "ls", "--tag", "shopping")
    assert "买牛奶" in out and "交报告" not in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "done", "1")
    assert code == 0 and "Done 1" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "ls")
    assert "买牛奶" not in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "ls", "--all")
    assert "[x] 1 买牛奶 #shopping" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "done", "1")
    assert code == 0 and "already done" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "reopen", "1")
    assert code == 0 and "Reopened 1" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "rm", "2")
    assert code == 0 and "Removed 2 交报告" in out

    code, out, _ = run(monkeypatch, capsys, tmp_path, "tags")
    assert out.strip() == "shopping (1)"

    code, out, _ = run(monkeypatch, capsys, tmp_path, "add", "再来一单", "--tag", "urgent")
    assert "Added #3" in out  # ids never reused


def test_exit_codes(monkeypatch, capsys, tmp_path):
    code, _, _ = run(monkeypatch, capsys, tmp_path, "rm", "7")
    assert code == 1

    code, _, err = run(monkeypatch, capsys, tmp_path, "rm", "7")
    assert "no task with id 7" in err

    code, _, _ = run(monkeypatch, capsys, tmp_path, "add", "   ")
    assert code == 2

    code, out, err = run(monkeypatch, capsys, tmp_path, "ls", "--tag", "ghost")
    assert code == 0
    assert out.strip() == "No matching tasks."
    assert "ghost" in err


def test_json_outputs(monkeypatch, capsys, tmp_path):
    run(monkeypatch, capsys, tmp_path, "add", "a", "--tag", "x")

    code, out, _ = run(monkeypatch, capsys, tmp_path, "ls", "--json")
    assert code == 0
    assert json.loads(out)[0]["title"] == "a"

    code, out, _ = run(monkeypatch, capsys, tmp_path, "tags", "--json")
    assert code == 0
    assert json.loads(out) == [{"tag": "x", "count": 1}]
