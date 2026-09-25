"""支持 ``python -m mock_server`` 直接运行（零安装试用）。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
