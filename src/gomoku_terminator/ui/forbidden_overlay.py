from __future__ import annotations

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.rules.renju_forbidden import forbidden_points


def current_forbidden_points(state: BitboardState, rule: str) -> list[tuple[int, int]]:
    """返回当前视图要绘制的禁手点。

    只有 Renju 规则显示黑棋禁手红色 X；自由五子棋模式不显示。
    """
    if rule != "renju":
        return []
    return forbidden_points(state)
