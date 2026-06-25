from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OpeningMove:
    """开局库命中结果。

    source 和 trust 必须保留，因为开局库是胜负关键资产，不能让低可信条目
    悄悄进入默认决策。
    """
    row: int
    col: int
    source: str
    trust: str


class OpeningBook:
    """JSON 开局库读取和查询。

    第一版只实现 key -> move 查询；后续会加入落子序列标准化、8 向对称扩展、
    来源质量过滤和版本校验。
    """
    def __init__(self, entries: dict[str, OpeningMove], metadata: dict[str, Any]) -> None:
        self.entries = entries
        self.metadata = metadata

    @classmethod
    def load(cls, path: str | Path) -> "OpeningBook":
        """从 JSON 文件加载开局库。"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        entries: dict[str, OpeningMove] = {}
        for item in data.get("entries", []):
            key = item["key"]
            move = item["move"]
            entries[key] = OpeningMove(
                row=int(move["row"]),
                col=int(move["col"]),
                source=str(item.get("source", "")),
                trust=str(item.get("trust", "unknown")),
            )
        return cls(entries, data)

    def lookup(self, key: str) -> OpeningMove | None:
        """按局面 key 查询推荐落子。"""
        return self.entries.get(key)
