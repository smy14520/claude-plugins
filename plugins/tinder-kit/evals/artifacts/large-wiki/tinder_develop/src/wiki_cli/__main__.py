"""支持 `python -m wiki_cli` 方式调用（与 `wiki` 入口等价）。"""

import sys

from wiki_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
