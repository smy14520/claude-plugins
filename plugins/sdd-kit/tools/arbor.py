#!/usr/bin/env python3
"""Compatibility shim for the sdd-kit Arbor CLI.

The implementation lives in arbor_core modules; keep this file as the stable
entry point used by docs, tests, and existing workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from arbor_core.cli import build_parser, main  # noqa: E402
from arbor_core.map_state import map_check  # noqa: E402
from arbor_core.package_state import list_packages, show_package  # noqa: E402
from arbor_core.validation import validate_package  # noqa: E402
from arbor_core.wiki_state import module_summary, wiki_collect, wiki_index, wiki_search  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
