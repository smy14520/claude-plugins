from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .map_model import ensure_map_workspace
from .map_sync import sync_map_from_packages


def contract_requests_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    requests = data.get("contract_requests")
    if not isinstance(requests, list):
        return []
    return [item for item in requests if isinstance(item, dict)]


def open_contract_requests_for_package(data: dict[str, Any], name: str) -> list[dict[str, Any]]:
    return [
        item
        for item in contract_requests_list(data)
        if item.get("status") in {"open", "accepted"} and name in {item.get("consumer"), item.get("producer")}
    ]


def next_contract_request_id(requests: list[dict[str, Any]]) -> str:
    current = 0
    for item in requests:
        raw = item.get("id")
        if isinstance(raw, str) and CONTRACT_REQUEST_ID_RE.match(raw):
            current = max(current, int(raw.split("-")[1]))
    return f"CR-{current + 1:03d}"


def record_contract_request(
    root: Path,
    initiative: str,
    consumer: str,
    producer: str,
    request: str,
    status: str,
    request_id: str | None,
    resolution: str | None,
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    validate_name(initiative)
    validate_name(consumer)
    validate_name(producer)
    if consumer == producer:
        raise ArborError("Contract request consumer and producer must be different packages.")
    if status not in CONTRACT_REQUEST_STATUSES:
        raise ArborError(f"Invalid contract request status '{status}'.")
    if request_id is not None and not CONTRACT_REQUEST_ID_RE.match(request_id):
        raise ArborError(f"Invalid contract request id '{request_id}'.")
    if not request.strip():
        raise ArborError("Contract request text is required.")

    ensure_map_workspace(root, initiative, timestamp)
    data = sync_map_from_packages(root, initiative, timestamp)
    package_names = {entry.get("name") for entry in data.get("packages", []) if isinstance(entry, dict)}
    for package_name, role in [(consumer, "consumer"), (producer, "producer")]:
        if package_name not in package_names:
            raise ArborError(f"Unknown {role} package '{package_name}' for initiative '{initiative}'.")

    requests = contract_requests_list(data)
    creating = request_id is None
    if creating:
        request_id = next_contract_request_id(requests)
        existing = None
    else:
        existing = next((item for item in requests if item.get("id") == request_id), None)

    if existing is None:
        if not creating:
            raise ArborError(f"Unknown contract request id '{request_id}'.")
        item = {
            "id": request_id,
            "consumer": consumer,
            "producer": producer,
            "request": request.strip(),
            "status": status,
            "resolution": resolution.strip() if isinstance(resolution, str) and resolution.strip() else None,
            "created_at": timestamp,
            "updated_at": timestamp,
            "created_by": actor,
            "updated_by": actor,
        }
        requests.append(item)
    else:
        existing["consumer"] = consumer
        existing["producer"] = producer
        existing["request"] = request.strip()
        existing["status"] = status
        if resolution is not None:
            existing["resolution"] = resolution.strip() or None
        existing["updated_at"] = timestamp
        existing["updated_by"] = actor
        item = existing

    data["contract_requests"] = requests
    data["updated_at"] = timestamp
    data.setdefault("history", []).append({"at": timestamp, "actor": actor, "event": "contract_request_recorded", "id": request_id, "consumer": consumer, "producer": producer, "status": status})
    write_json(map_json_path(root, initiative), data)
    return {"initiative": initiative, "map_json": f".arbor/maps/{initiative}/map.json", "contract_request": item}
