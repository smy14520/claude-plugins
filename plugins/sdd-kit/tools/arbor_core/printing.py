from __future__ import annotations

from typing import Any


def print_human_list(items: list[dict[str, Any]]) -> None:
    if not items:
        print("未找到 package。")
        return
    for item in items:
        next_action = item.get("next_action") or {}
        print(
            f"{item['name']}\tstate={item.get('state')}\tphase={item.get('current_phase')}\tsizing={item.get('package_sizing')}\t"
            f"next={next_action.get('skill')}\texec={item.get('execution_status')} branch={item.get('branch')} pr={item.get('pr')}"
        )


def print_human_show(data: dict[str, Any]) -> None:
    print(f"Package: {data['name']}")
    print(f"路径: {data['package']}")
    print(f"状态: {data.get('state')}")
    print(f"阶段: {data.get('current_phase')}")
    print(f"下一步: {data.get('next_action')}")
    print(f"Package sizing: {data.get('package_sizing')}")
    print(f"Execution: {data.get('execution')}")
    print(f"PRD: {data.get('prd')}")
    slices = data.get("slices")
    if slices:
        print("Slices:")
        for s in slices:
            note = f" — {s['note']}" if s.get("note") else ""
            print(f"  {s['id']}: {s['status']}{note}")
    print(f"Impl result: {data.get('impl_result')}")
    print(f"Review result: {data.get('review_result')}")
    print(f"Validation: {'ok' if data['validation']['ok'] else 'failed'}")
    for error in data["validation"]["errors"]:
        print(f"  - {error}")


def print_human_doctor(data: dict[str, Any]) -> None:
    packages = data.get("packages", {}) if isinstance(data.get("packages"), dict) else {}
    print("Arbor doctor")
    print("")
    print(f"Packages: {'ok' if packages.get('ok') else 'failed'}")
    next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else {}
    if next_action:
        print(f"Next action: {next_action.get('skill')} {next_action.get('package') or ''} — {next_action.get('reason')}")
    package_errors = packages.get("errors", {}) if isinstance(packages.get("errors"), dict) else {}
    if package_errors:
        print("")
        print("Package errors:")
        for name, errors in package_errors.items():
            for error in errors:
                print(f"  - {name}: {error}")

    print("")
    print("Result: " + ("ok" if data.get("ok") else "failed"))
