from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move

CENTER = BOARD_SIZE // 2


def ordered_moves(state: BitboardState, color: int = BLACK, rule: str = "renju") -> list[tuple[int, int]]:
    """返回排序后的候选点。

    当前先用中心优先，保证搜索能跑。后续要改成“成五、防五、冲四、活三、
    双威胁、禁手过滤、邻域半径”的强排序，这是 Alpha-Beta 剪枝效率的关键。
    """
    skip_forbidden_scan = rule != "renju" or color != BLACK or _black_stone_count(state) < 4
    moves = []
    for row, col in state.legal_empty_points():
        if not skip_forbidden_scan and is_forbidden_move(state, row, col):
            continue
        moves.append((row, col))
    moves.sort(key=lambda point: abs(point[0] - CENTER) + abs(point[1] - CENTER))
    return moves


def _black_stone_count(state: BitboardState) -> int:
    """统计黑棋数量。

    黑棋数量很少时不可能形成三三、四四或长连，提前跳过禁手扫描可以让开局
    候选点生成保持轻量。
    """

    return sum(int(word).bit_count() for word in state.black)
