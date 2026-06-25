from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from gomoku_terminator.board.bitboard import BLACK, WHITE
from gomoku_terminator.opening.symmetry import transform_point

MoveLike = Any


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
            key = item.get("key") or sequence_key(item["sequence"])
            move = item["move"]
            opening_move = OpeningMove(
                row=int(move["row"]),
                col=int(move["col"]),
                source=str(item.get("source", "")),
                trust=str(item.get("trust", "unknown")),
            )
            entries[key] = opening_move
            if item.get("expand_symmetry", False):
                for transform in _TRANSFORMS:
                    transformed_sequence = [
                        {
                            "color": move_item["color"],
                            "row": transform_point(int(move_item["row"]), int(move_item["col"]), transform)[0],
                            "col": transform_point(int(move_item["row"]), int(move_item["col"]), transform)[1],
                        }
                        for move_item in item["sequence"]
                    ]
                    transformed_row, transformed_col = transform_point(opening_move.row, opening_move.col, transform)
                    transformed_key = sequence_key(transformed_sequence)
                    entries.setdefault(
                        transformed_key,
                        OpeningMove(
                            row=transformed_row,
                            col=transformed_col,
                            source=opening_move.source,
                            trust=opening_move.trust,
                        ),
                    )
        return cls(entries, data)

    def lookup(self, key: str) -> OpeningMove | None:
        """按局面 key 查询推荐落子。"""
        return self.entries.get(key)

    def lookup_moves(self, moves: Iterable[MoveLike]) -> OpeningMove | None:
        """按当前对局历史查询推荐落子。

        开局库的键必须只依赖棋谱历史，不能依赖 UI 或搜索内部状态。这样同一局面
        在人机、机机、复盘和测试里都能稳定命中。
        """

        return self.lookup(sequence_key(moves))


def sequence_key(moves: Iterable[MoveLike]) -> str:
    """把落子序列编码成稳定字符串 key。

    格式示例：`B7,7|W6,7`。这里故意使用 0-based row/col，和项目日志、
    bitboard、UI 坐标保持一致，避免在热点链路里反复转换。
    """

    parts: list[str] = []
    for move in moves:
        color = _move_value(move, "color")
        row = int(_move_value(move, "row"))
        col = int(_move_value(move, "col"))
        color_text = "B" if _normalize_color(color) == BLACK else "W"
        parts.append(f"{color_text}{row},{col}")
    return "|".join(parts)


def _move_value(move: MoveLike, name: str) -> Any:
    """兼容 dataclass Move 和 JSON dict 两种落子表示。"""

    if isinstance(move, dict):
        return move[name]
    return getattr(move, name)


def _normalize_color(color: Any) -> int:
    """把日志/JSON/内部常量里的颜色统一成 BLACK/WHITE。"""

    if color in (BLACK, "black", "B", "b", 1):
        return BLACK
    if color in (WHITE, "white", "W", "w", 2):
        return WHITE
    raise ValueError(f"unknown opening move color: {color}")


_TRANSFORMS = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "flip_h",
    "flip_v",
    "diag_main",
    "diag_anti",
)
