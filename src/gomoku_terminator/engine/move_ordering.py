from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE, POINT_COUNT, index_to_row_col
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move
from gomoku_terminator.rules.win_check import DIRECTIONS, count_line, has_five_from

CENTER = BOARD_SIZE // 2


def ordered_moves(state: BitboardState, color: int = BLACK, rule: str = "renju") -> list[tuple[int, int]]:
    """返回排序后的候选点。

    候选点只取已有棋子周围半径 2 的空点。五子棋搜索的分支控制非常关键，
    全盘 225 点每层都扫会直接拖垮 Alpha-Beta；邻域候选能保留大多数有意义
    落点，同时显著降低分支数。
    """
    skip_forbidden_scan = rule != "renju" or color != BLACK or _black_stone_count(state) < 4
    moves = []
    for row, col in _nearby_empty_points(state):
        if not skip_forbidden_scan and is_forbidden_move(state, row, col):
            continue
        moves.append((row, col))
    moves.sort(key=lambda point: _move_priority(state, point, color))
    return moves


def _black_stone_count(state: BitboardState) -> int:
    """统计黑棋数量。

    黑棋数量很少时不可能形成三三、四四或长连，提前跳过禁手扫描可以让开局
    候选点生成保持轻量。
    """

    return sum(int(word).bit_count() for word in state.black)


def _nearby_empty_points(state: BitboardState, radius: int = 2) -> list[tuple[int, int]]:
    """生成已有棋子附近的空点。

    空棋盘时直接返回天元。否则只考虑棋子周围 `radius` 范围内的空点，
    这是搜索速度能起来的第一道闸门。
    """

    occupied: list[tuple[int, int]] = []
    for index in range(POINT_COUNT):
        if state.occupied_at_index(index):
            occupied.append(index_to_row_col(index))

    if not occupied:
        return [(CENTER, CENTER)]

    points: set[tuple[int, int]] = set()
    for row, col in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                r = row + dr
                c = col + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and state.is_empty_at(r, c):
                    points.add((r, c))
    return list(points)


def _move_priority(state: BitboardState, point: tuple[int, int], color: int) -> tuple[int, int, int]:
    """候选点排序优先级。

    分数越高越靠前。排序首先关注立即胜、防对方立即胜、长连形和开放端，
    再用中心距离和坐标做稳定排序。
    """

    row, col = point
    score = _candidate_score(state, row, col, color)
    return -score, abs(row - CENTER) + abs(col - CENTER), row * BOARD_SIZE + col


def _candidate_score(state: BitboardState, row: int, col: int, color: int) -> int:
    """给候选落点做轻量战术打分。

    这里只用局部连线和一步胜检查，不做深层搜索。目标是让 Alpha-Beta 先看
    明显强手，提升剪枝效率。
    """

    opponent = WHITE if color == BLACK else BLACK
    own = state.copy()
    own.place(row, col, color)
    if has_five_from(own, row, col, color):
        return 1_000_000

    block = state.copy()
    block.place(row, col, opponent)
    if has_five_from(block, row, col, opponent):
        return 900_000

    best_line = 0
    best_open = 0
    for dr, dc in DIRECTIONS:
        length = count_line(own, row, col, color, dr, dc)
        open_ends = _open_ends(own, row, col, color, dr, dc, length)
        if length > best_line or (length == best_line and open_ends > best_open):
            best_line = length
            best_open = open_ends

    shape_score = {
        (4, 2): 120_000,
        (4, 1): 35_000,
        (3, 2): 12_000,
        (3, 1): 2_000,
        (2, 2): 500,
        (2, 1): 100,
    }.get((min(best_line, 4), best_open), 0)
    return shape_score


def _open_ends(state: BitboardState, row: int, col: int, color: int, dr: int, dc: int, length: int) -> int:
    """计算候选落子形成线段的开放端数量。"""

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
    if 0 <= before_r < BOARD_SIZE and 0 <= before_c < BOARD_SIZE and state.is_empty_at(before_r, before_c):
        open_ends += 1
    if 0 <= after_r < BOARD_SIZE and 0 <= after_c < BOARD_SIZE and state.is_empty_at(after_r, after_c):
        open_ends += 1
    return open_ends
