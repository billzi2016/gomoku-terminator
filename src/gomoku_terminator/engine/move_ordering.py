from __future__ import annotations

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE

CENTER = BOARD_SIZE // 2


def ordered_moves(state: BitboardState) -> list[tuple[int, int]]:
    """返回排序后的候选点。

    当前先用中心优先，保证搜索能跑。后续要改成“成五、防五、冲四、活三、
    双威胁、禁手过滤、邻域半径”的强排序，这是 Alpha-Beta 剪枝效率的关键。
    """
    moves = state.legal_empty_points()
    moves.sort(key=lambda point: abs(point[0] - CENTER) + abs(point[1] - CENTER))
    return moves
