"""体检：死链、孤岛页面、重复标题（Q14/Q15）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import WikiIndex


@dataclass
class DoctorReport:
    dead_links: list[tuple[str, str]] = field(default_factory=list)  # (源页面, 目标)
    orphans: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        """死链与重复标题是身份层面的阻断发现；孤岛默认仅警告（Q15）。"""
        return bool(self.dead_links or self.duplicates)


def diagnose(index: WikiIndex, ignore: set[str] | None = None) -> DoctorReport:
    ignore = ignore or set()
    title_map = index.title_map()
    dead: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    inbound: dict[str, int] = {}
    for page in index.pages:
        for target in page.links:
            matches = title_map.get(target)
            if not matches:
                pair = (page.title, target)
                if pair not in seen:
                    seen.add(pair)
                    dead.append(pair)
                continue
            if target == page.title:
                continue  # 自链接不计入入链（一致性裁定 ③）
            for _ in matches:
                inbound[target] = inbound.get(target, 0) + 1
    orphans = [
        page.title
        for page in index.pages
        if inbound.get(page.title, 0) == 0 and page.title not in ignore
    ]
    duplicates = sorted(t for t, group in title_map.items() if len(group) > 1)
    return DoctorReport(sorted(set(dead)), sorted(set(orphans)), duplicates)
