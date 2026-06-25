from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.rules.win_check import has_winner

WIN_SCORE = 1_000_000


def evaluate(state: BitboardState, color: int) -> int:
    """静态评估函数。

    现在只是占位级评估：赢棋给极大分，否则比较双方棋子数。真正要和高手下，
    这里后续必须替换为棋形、威胁、禁手、攻防优先级共同驱动的高质量评估。
    """
    opponent = WHITE if color == BLACK else BLACK
    if has_winner(state, color):
        return WIN_SCORE
    if has_winner(state, opponent):
        return -WIN_SCORE
    return _stone_count(state, color) - _stone_count(state, opponent)


def _stone_count(state: BitboardState, color: int) -> int:
    """统计某方棋子数量。"""
    bits = state.black if color == BLACK else state.white
    return sum(int(word).bit_count() for word in bits)
