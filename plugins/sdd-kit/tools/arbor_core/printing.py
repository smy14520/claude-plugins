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
    print(f"Impl result: {data.get('impl_result')}")
    print(f"Review result: {data.get('review_result')}")
    print(f"Validation: {'ok' if data['validation']['ok'] else 'failed'}")
    for error in data["validation"]["errors"]:
        print(f"  - {error}")


def print_human_wiki_lint(data: dict[str, Any]) -> None:
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    print(f"Wiki: {data.get('wiki_root')}")
    print(f"Errors: {summary.get('error_count', 0)}")
    for issue in data.get("errors", []):
        print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")
    print(f"Warnings: {summary.get('warning_count', 0)}")
    for issue in data.get("warnings", []):
        print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")


def print_human_doctor(data: dict[str, Any]) -> None:
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    packages = data.get("packages", {}) if isinstance(data.get("packages"), dict) else {}
    wiki = data.get("wiki", {}) if isinstance(data.get("wiki"), dict) else {}
    print("Arbor doctor")
    print("")
    print(f"Packages: {'ok' if packages.get('ok') else 'failed'}")
    if wiki.get("skipped"):
        print(f"Wiki: skipped ({wiki.get('wiki_root')})")
    else:
        wiki_summary = wiki.get("summary", {}) if isinstance(wiki.get("summary"), dict) else {}
        wiki_status = "ok" if wiki.get("ok") else "failed"
        print(f"Wiki: {wiki_status} ({wiki_summary.get('warning_count', 0)} warnings)")
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

    wiki_errors = wiki.get("errors", []) if isinstance(wiki.get("errors"), list) else []
    wiki_warnings = wiki.get("warnings", []) if isinstance(wiki.get("warnings"), list) else []
    if wiki_errors:
        print("")
        print("Wiki errors:")
        for issue in wiki_errors:
            print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")
    if wiki_warnings:
        print("")
        print("Wiki warnings:")
        for issue in wiki_warnings:
            print(f"  - {issue.get('path')} [{issue.get('code')}] {issue.get('message')}")

    print("")
    print("Result: " + ("ok" if data.get("ok") else "failed"))
