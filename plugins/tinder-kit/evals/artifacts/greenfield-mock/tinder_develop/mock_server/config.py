"""Contract loading: turns mocks.json into Route objects."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A path parameter is a single segment of the form {name}.
PATH_PARAMETER_RE = re.compile(r"^\{([A-Za-z_][A-Za-z0-9_]*)\}$")


@dataclass(frozen=True)
class Route:
    """One mocked route: method + path template + static response."""

    method: str
    path_template: str
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


class ConfigError(Exception):
    """Raised when the contract file cannot be read or parsed structurally."""


def parse_contract(path: str | Path) -> tuple[list[dict] | None, str | None]:
    """Read mocks.json and return its raw route objects, or an error message.

    Shared head of load_config() and check_file(): file reading, JSON
    parsing and the top-level shape checks, so both report identical
    file-level problems.
    """
    contract = Path(path)
    try:
        raw = contract.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{contract}: cannot read file ({exc.strerror})"
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"{contract}: invalid JSON ({exc.msg}, line {exc.lineno})"
    if not isinstance(doc, dict):
        return None, f"{contract}: top level must be an object"
    routes = doc.get("routes")
    if not isinstance(routes, list):
        return None, f'{contract}: "routes" must be an array'
    return routes, None


def load_config(path: str | Path) -> list[Route]:
    """Read a mocks.json contract and return its routes in file order."""
    raw_routes, error = parse_contract(path)
    if error is not None:
        raise ConfigError(error)

    routes: list[Route] = []
    for index, item in enumerate(raw_routes, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"route[{index}] must be an object")
        method = item.get("method")
        template = item.get("path")
        if not isinstance(method, str) or not isinstance(template, str):
            raise ConfigError(f'route[{index}] requires string "method" and "path"')
        headers = item.get("headers") or {}
        if not _is_string_map(headers):
            raise ConfigError(f'route[{index}]: "headers" must map strings to strings')
        routes.append(Route(
            method=method,
            path_template=template,
            status=item.get("status", 200),
            headers=dict(headers),
            body=item.get("body"),
        ))
    return routes


def _is_string_map(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    )
