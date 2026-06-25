from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def count_line(state: BitboardState, row: int, col: int, color: int, dr: int, dc: int) -> int:
    """统计某个方向上的连续同色棋子数。

    `(dr, dc)` 表示方向，例如 `(0, 1)` 是横向，`(1, 1)` 是主对角线。
    函数会同时向正反两个方向延伸，所以返回的是包含当前点在内的整条连续长度。
    """
    total = 1
    for sign in (-1, 1):
        r = row + sign * dr
        c = col + sign * dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and state.color_at(r, c) == color:
            total += 1
            r += sign * dr
            c += sign * dc
    return total


def has_five_from(state: BitboardState, row: int, col: int, color: int) -> bool:
    """判断指定点是否形成五连或更多。

    普通五子棋可以用这个判断胜负；Renju 黑棋还需要区分“正好五连”和“长连禁手”。
    """
    if color not in (BLACK, WHITE):
        raise ValueError(f"invalid color: {color}")
    if state.color_at(row, col) != color:
        return False
    return any(count_line(state, row, col, color, dr, dc) >= 5 for dr, dc in DIRECTIONS)


def has_exact_five_from(state: BitboardState, row: int, col: int, color: int) -> bool:
    """判断指定点是否形成正好五连。

    这个函数是 Renju 规则的基础：黑棋六连以上不是普通胜利，而要进入长连禁手判断。
    """
    if color not in (BLACK, WHITE):
        raise ValueError(f"invalid color: {color}")
    if state.color_at(row, col) != color:
        return False
    return any(count_line(state, row, col, color, dr, dc) == 5 for dr, dc in DIRECTIONS)


def has_winner(state: BitboardState, color: int) -> bool:
    """扫描全盘判断某方是否已有五连。"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if has_five_from(state, row, col, color):
                return True
    return False
