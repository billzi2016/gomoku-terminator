from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, EMPTY, WHITE, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE
from gomoku_terminator.rules.win_check import DIRECTIONS, count_line, has_winner

WIN_SCORE = 1_000_000
PATTERN_SCORES = {
    (5, 0): WIN_SCORE,
    (4, 2): 120_000,
    (4, 1): 25_000,
    (3, 2): 8_000,
    (3, 1): 1_200,
    (2, 2): 400,
    (2, 1): 80,
}


def evaluate(state: BitboardState, color: int) -> int:
    """静态评估函数。

    第一版棋形评估：赢棋给极大分，否则按连续棋形、两端开放程度和中心控制
    打分。它还不是职业级，但已经比单纯数棋子更接近五子棋搜索需要的信号。
    """
    opponent = WHITE if color == BLACK else BLACK
    if has_winner(state, color):
        return WIN_SCORE
    if has_winner(state, opponent):
        return -WIN_SCORE
    return _shape_score(state, color) - _shape_score(state, opponent) + _center_score(state, color)


def _stone_count(state: BitboardState, color: int) -> int:
    """统计某方棋子数量。"""
    bits = state.black if color == BLACK else state.white
    return sum(int(word).bit_count() for word in bits)


def _shape_score(state: BitboardState, color: int) -> int:
    """统计某方全盘棋形分。

    为避免同一条连续棋形被重复统计，只从每条线段的起点开始计分。
    """

    score = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if state.color_at(row, col) != color:
                continue
            for dr, dc in DIRECTIONS:
                prev_r = row - dr
                prev_c = col - dc
                if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE:
                    if state.color_at(prev_r, prev_c) == color:
                        continue
                length = count_line(state, row, col, color, dr, dc)
                if length < 2:
                    continue
                open_ends = _open_ends(state, row, col, color, dr, dc, length)
                score += PATTERN_SCORES.get((min(length, 5), open_ends), 0)
    score += _stone_count(state, color) * 3
    return score


def _open_ends(state: BitboardState, row: int, col: int, color: int, dr: int, dc: int, length: int) -> int:
    """计算连续棋形两端是否开放。

    开放端越多，棋形攻击价值越高。活三、活四比眠三、冲四更有杀伤力。
    """

    start_r = row
    start_c = col
    while 0 <= start_r - dr < BOARD_SIZE and 0 <= start_c - dc < BOARD_SIZE:
        if state.color_at(start_r - dr, start_c - dc) != color:
            break
        start_r -= dr
        start_c -= dc

    end_r = start_r + dr * (length - 1)
    end_c = start_c + dc * (length - 1)
    open_ends = 0
    before_r = start_r - dr
    before_c = start_c - dc
    after_r = end_r + dr
    after_c = end_c + dc
    if 0 <= before_r < BOARD_SIZE and 0 <= before_c < BOARD_SIZE and state.color_at(before_r, before_c) == EMPTY:
        open_ends += 1
    if 0 <= after_r < BOARD_SIZE and 0 <= after_c < BOARD_SIZE and state.color_at(after_r, after_c) == EMPTY:
        open_ends += 1
    return open_ends


def _center_score(state: BitboardState, color: int) -> int:
    """中心控制分。

    开局和中盘中心附近通常更有价值，这个轻量分数给搜索一个稳定偏好。
    """

    center = BOARD_SIZE // 2
    score = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if state.color_at(row, col) == color:
                score += max(0, 14 - (abs(row - center) + abs(col - center)))
    return score
