# todo

单文件 Todo CLI（Python 3 标准库 + pytest）。运行测试：`python3 -m pytest -q`。

## Agent skills

### Issue tracker
Local markdown issue tracker. See `.forge/issue-tracker.md`.

### Triage labels
Standard triage labels. See `.forge/triage-labels.md`.

### Domain docs
Single-context layout: CONTEXT.md in .forge/, ADRs in .forge/wiki/decision/. See `.forge/domain.md`.

### Wiki
Before assessing a change's impact, modifying non-trivial code, or answering "why is it like this", check `.forge/wiki/` via the `wiki` skill: it records cross-module couplings, decisions and gotchas the code doesn't show.

When a decision or fact in the conversation contradicts a recorded glossary term, ADR, or wiki entry, call it out: "ADR-0003 says X, but you're now deciding Y. Which holds?" Once settled, rewrite that record in place to state what is true now, with one line noting what it was and why it changed.
