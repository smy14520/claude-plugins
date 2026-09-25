"""支持 `python -m todo_cli` 直跑。"""

import sys

from .cli import main

sys.exit(main())
