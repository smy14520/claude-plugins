# todo-cli

`todo` is a project-local todo CLI. It keeps one plain JSON file, `./.todos.json`,
in the current directory — committable, greppable, hand-editable — and nothing
else: no service, no database, no runtime dependencies beyond the standard
library (Python >= 3.12).

```console
$ todo add "修登录" --tag backend,urgent -p high
Added #1 修登录

$ todo list
#1 [ ] high @backend @urgent 修登录

$ todo done 1
$ todo list --all
#1 [x] high @backend @urgent 修登录

$ todo clear          # delete every completed todo
$ todo rm 2           # delete one todo
$ todo edit 1 --title "新标题" -p low --tag x
$ todo list --json    # same filter + order, JSON array on stdout
```

## Command surface

| Command | Form | Notes |
|---|---|---|
| `add` | `todo add "标题" [--tag T]... [-p high\|med\|low]` | prints the new id; `--tag` repeatable, comma-split |
| `list` | `todo list [--tag T]... [--priority P] [--all] [--json]` | pending only unless `--all` |
| `done` / `reopen` | `todo done <id>` / `todo reopen <id>` | the only paths between pending and done |
| `rm` | `todo rm <id>` | single delete, ids are never reused |
| `edit` | `todo edit <id> [--title S] [--tag T]... [-p P]` | changes only the given fields; `--tag` replaces the whole set |
| `clear` | `todo clear` | deletes every completed todo |

Semantics: filters intersect (multiple `--tag` mean AND), one sort rule for every
view (pending by priority then id; completed after all pending, newest first),
`--json` renders the same result as the text view, stdout carries data only, and
errors go to stderr with a non-zero exit code. An empty result is not an error.

## Development

```console
$ uv sync                      # create .venv, install dev group
$ uv run pytest                # test suite
$ uv run ruff check .          # lint
```
