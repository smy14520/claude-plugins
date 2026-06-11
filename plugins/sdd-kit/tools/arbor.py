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

from arbor_core.brainstorm_finalize import finalize_brainstorm  # noqa: E402
from arbor_core.cli import build_parser, main  # noqa: E402
from arbor_core.doctor import doctor  # noqa: E402
from arbor_core.module_summary import module_summary  # noqa: E402
from arbor_core.package_checks import derive_required_checks, record_check, run_check  # noqa: E402
from arbor_core.package_packet import impl_packet  # noqa: E402
from arbor_core.package_results import record_impl_result, record_review  # noqa: E402
from arbor_core.package_state import list_packages, show_package  # noqa: E402
from arbor_core.validation import validate_package  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
