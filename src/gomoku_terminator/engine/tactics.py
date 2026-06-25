from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.move_ordering import ordered_moves
from gomoku_terminator.rules.win_check import has_five_from


def immediate_win_move(state: BitboardState, color: int, rule: str = "renju") -> tuple[int, int] | None:
    """寻找当前方一步成五的落点。

    这是搜索前最重要的战术检查：如果已经能一手赢，就不要浪费时间进入深搜。
    """

    wins = immediate_win_moves(state, color, rule)
    return wins[0] if wins else None


def immediate_win_moves(state: BitboardState, color: int, rule: str = "renju") -> list[tuple[int, int]]:
    """列出当前方所有一步成五点。

    多个一步胜点意味着“双杀”或更强的不可全防威胁，是基础 VCF/VCT 的重要信号。
    """

    wins: list[tuple[int, int]] = []
    for row, col in ordered_moves(state, color, rule):
        probe = state.copy()
        probe.place(row, col, color)
        if has_five_from(probe, row, col, color):
            wins.append((row, col))
    return wins


def immediate_block_move(state: BitboardState, color: int, rule: str = "renju") -> tuple[int, int] | None:
    """寻找必须防守的对方一步成五点。

    如果对手下一手能赢，当前方优先堵住该点。更复杂的双杀防守后续交给 VCF/VCT。
    """

    opponent = WHITE if color == BLACK else BLACK
    return immediate_win_move(state, opponent, rule)


def double_threat_move(state: BitboardState, color: int, rule: str = "renju") -> tuple[int, int] | None:
    """寻找一手制造两个及以上一步胜点的落子。

    这不是完整 VCF，但已经能识别很多“一手双杀”：对手下一手最多只能挡一个点，
    如果我方同时产生两个成五点，对手通常无法全部防住。
    """

    for row, col in ordered_moves(state, color, rule):
        probe = state.copy()
        probe.place(row, col, color)
        if len(immediate_win_moves(probe, color, rule)) >= 2:
            return row, col
    return None
