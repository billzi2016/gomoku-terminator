from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.move_ordering import ordered_moves
from gomoku_terminator.rules.win_check import has_five_from


def immediate_win_move(state: BitboardState, color: int, rule: str = "renju") -> tuple[int, int] | None:
    """寻找当前方一步成五的落点。

    这是搜索前最重要的战术检查：如果已经能一手赢，就不要浪费时间进入深搜。
    """

    for row, col in ordered_moves(state, color, rule):
        probe = state.copy()
        probe.place(row, col, color)
        if has_five_from(probe, row, col, color):
            return row, col
    return None


def immediate_block_move(state: BitboardState, color: int, rule: str = "renju") -> tuple[int, int] | None:
    """寻找必须防守的对方一步成五点。

    如果对手下一手能赢，当前方优先堵住该点。更复杂的双杀防守后续交给 VCF/VCT。
    """

    opponent = WHITE if color == BLACK else BLACK
    return immediate_win_move(state, opponent, rule)
