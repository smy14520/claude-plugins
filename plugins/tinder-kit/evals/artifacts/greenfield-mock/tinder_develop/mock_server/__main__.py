"""Entry point for `python -m mock_server`."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
