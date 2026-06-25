from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE, POINT_COUNT, index_to_row_col
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move

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
    moves.sort(key=_move_priority)
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


def _move_priority(point: tuple[int, int]) -> tuple[int, int]:
    """候选点排序优先级。

    当前先用中心距离和坐标稳定排序；后续会在这里接入成五、防五、冲四、
    活三、双威胁等强排序特征。
    """

    row, col = point
    return abs(row - CENTER) + abs(col - CENTER), row * BOARD_SIZE + col
