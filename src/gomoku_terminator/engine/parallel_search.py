from __future__ import annotations

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.engine.negamax import SearchResult, search_best_move


def parallel_root_search(
    state: BitboardState,
    color: int,
    depth: int,
    time_limit: float,
    rule: str = "renju",
) -> SearchResult:
    """根节点并行搜索入口。

    现在先委托单线程搜索，保持接口稳定。后续这里会换成 Numba `prange`
    根节点分发，目标是在 M2 Ultra 上吃满 24 核。
    """
    return search_best_move(state, color, depth, time_limit, rule)
