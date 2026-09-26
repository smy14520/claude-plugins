"""Static contract checking: the five check rules, reported not raised."""
from __future__ import annotations

from pathlib import Path

from .config import PATH_PARAMETER_RE, parse_contract

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE")


def check_file(path: str | Path) -> list[str]:
    """Check a mocks.json contract and return one message per problem.

    An empty list means the contract is valid. Content problems are
    reported as messages; routes are never built into Route objects here.
    """
    raw_routes, error = parse_contract(path)
    if error is not None:
        return [error]

    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(raw_routes, start=1):
        errors.extend(_check_route(index, item, seen))
    return errors


def _check_route(index: int, item: object, seen: set[tuple[str, str]]) -> list[str]:
    label = f"route[{index}]"
    if not isinstance(item, dict):
        return [f"{label} must be an object"]

    errors: list[str] = []

    method = item.get("method")
    if not isinstance(method, str) or method not in HTTP_METHODS:
        errors.append(f'{label}: "method" must be one of {" ".join(HTTP_METHODS)}')

    template = item.get("path")
    if not isinstance(template, str) or not template.startswith("/"):
        errors.append(f'{label}: "path" is required and must start with "/"')
        template = None
    else:
        for part in template.split("/")[1:]:
            if "{" in part and PATH_PARAMETER_RE.match(part) is None:
                errors.append(
                    f'{label}: invalid path parameter "{part}" '
                    "(expected {{name}} with letters, digits, underscores)"
                )

    status = item.get("status", 200)
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
        errors.append(f'{label}: "status" must be an integer between 100 and 599')

    if isinstance(method, str) and isinstance(template, str):
        key = (method, template)
        if key in seen:
            errors.append(f"{label}: duplicate route {method} {template}")
        seen.add(key)

    return errors
