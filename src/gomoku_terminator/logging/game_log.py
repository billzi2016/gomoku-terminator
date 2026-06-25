from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time


@dataclass(frozen=True)
class MoveLog:
    """单步对局日志。

    对局文件使用普通 JSON，并用 `indent=2` 保存，方便人工检查和复盘调试。
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
    """JSON 对局日志写入器。

    当前实现每次追加后重写整个 JSON 文件。五子棋最多 225 手，这个成本可以接受，
    换来的是文件结构清晰、可读性强，并且满足 `indent=2` 的保存要求。
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"version": 1, "moves": []})

    def append(self, record: MoveLog) -> None:
        """追加一条日志记录。"""

        data = self.read()
        data.setdefault("moves", []).append(asdict(record))
        self._write(data)

    def read(self) -> dict:
        """读取当前日志文件。"""

        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: dict) -> None:
        """以缩进 2 个空格写回 JSON 文件。"""

        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
