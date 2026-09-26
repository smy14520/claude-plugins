"""支持 `python -m todo` 直接运行。"""

import sys

from todo.cli import main

if __name__ == "__main__":
    sys.exit(main())
