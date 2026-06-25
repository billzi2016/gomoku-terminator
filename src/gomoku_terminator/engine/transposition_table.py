from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TTEntry:
    """置换表条目。

    key 用于确认局面，depth/score/flag/best_move 用于深层搜索剪枝和走法排序。
    """
    key: int
    depth: int
    score: int
    flag: int
    best_move: int


class TranspositionTable:
    """开发期字典版置换表。

    正式高性能版本会替换成一维 NumPy 数组，允许 lock-free 覆盖写。
    """
    def __init__(self) -> None:
        self._table: dict[int, TTEntry] = {}

    def get(self, key: int) -> TTEntry | None:
        """查询局面缓存。"""
        return self._table.get(key)

    def store(self, entry: TTEntry) -> None:
        """写入局面缓存。"""
        self._table[entry.key] = entry
