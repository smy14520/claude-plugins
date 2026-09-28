"""库存数据：{商品名: 数量}，以单个 JSON 文件持久化。"""

import json
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict[str, int]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, items: dict[str, int]) -> None:
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
