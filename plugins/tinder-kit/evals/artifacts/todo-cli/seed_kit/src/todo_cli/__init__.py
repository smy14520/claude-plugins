"""Project-local todo CLI backed by a single ``./.todos.json`` file.

Layers (see ``.arbor/.wiki/module/todo-cli.md``):

- :mod:`todo_cli.store` -- schema, load/save of ``./.todos.json``, atomic writes.
- :mod:`todo_cli.core` -- record semantics, lifecycle transitions, filter + order.
- :mod:`todo_cli.cli` -- argparse parsing, rendering, exit codes.
"""

__version__ = "0.1.0"
