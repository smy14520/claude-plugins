"""Allow ``python -m todo_cli`` alongside the ``todo`` console script."""

import sys

from .cli import main

sys.exit(main())
