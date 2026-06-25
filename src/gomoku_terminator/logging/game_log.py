from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time


@dataclass(frozen=True)
class MoveLog:
    """单步对局日志。

    一步一行 JSON Lines，确保人机、机机和异常情况都能完整复盘。
    """
    game_id: str
    move_number: int
    player: str
    row: int
    col: int
    index: int
    rule: str
    is_forbidden: bool
    forbidden_points: list[tuple[int, int]]
    search_depth: int
    nodes: int
    nps: float
    score: int
    time_ms: float
    engine: str
    timestamp: float

    @classmethod
    def create(
        cls,
        game_id: str,
        move_number: int,
        player: str,
        row: int,
        col: int,
        index: int,
        rule: str,
    ) -> "MoveLog":
        """创建一条最小落子日志。

        搜索深度、节点数、评分等字段可以在 AI 接入后补齐。
        """
        return cls(game_id, move_number, player, row, col, index, rule, False, [], 0, 0, 0.0, 0, 0.0, "", time())


class GameLogWriter:
    """JSON Lines 对局日志写入器。"""
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: MoveLog) -> None:
        """追加一条日志记录。"""
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
