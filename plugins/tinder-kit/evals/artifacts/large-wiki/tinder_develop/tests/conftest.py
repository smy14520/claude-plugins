"""Shared fixtures: throwaway vaults built from {relative_path: content}."""
from pathlib import Path

import pytest

from wikicli.index import load_vault


@pytest.fixture
def make_vault(tmp_path):
    """Build a throwaway vault from {relative_path: content} and return its root."""

    def _make(files: dict[str, str]) -> Path:
        for rel, content in files.items():
            target = tmp_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return tmp_path

    return _make


@pytest.fixture
def vault_of(make_vault):
    """Like ``make_vault`` but returns the loaded ``Vault`` index."""

    def _vault(files: dict[str, str]):
        return load_vault(make_vault(files))

    return _vault
