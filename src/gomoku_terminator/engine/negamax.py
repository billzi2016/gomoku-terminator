from __future__ import annotations

from dataclasses import dataclass

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.evaluator import evaluate
from gomoku_terminator.engine.move_ordering import ordered_moves
from gomoku_terminator.engine.tactics import immediate_block_move, immediate_win_move
from gomoku_terminator.engine.time_control import TimeControl


@dataclass(frozen=True)
class SearchResult:
    """搜索返回结果。

    UI、日志、机机模式都需要这一组信息：落点、评分、深度和节点数。
    """
    row: int
    col: int
    score: int
    depth: int
    nodes: int


def search_best_move(
    state: BitboardState,
    color: int,
    depth: int,
    time_limit: float,
    rule: str = "renju",
) -> SearchResult:
    """搜索当前最佳落子。

    这是清晰版单线程 Negamax 入口。后续 Numba/并行搜索会保持类似返回契约，
    这样 UI、日志和 benchmark 不需要跟着搜索实现大改。
    """
    nodes = 0
    best_score = -10**9
    win_move = immediate_win_move(state, color, rule)
    if win_move is not None:
        return SearchResult(win_move[0], win_move[1], 10**9, depth, 1)
    block_move = immediate_block_move(state, color, rule)
    if block_move is not None:
        return SearchResult(block_move[0], block_move[1], 500_000, depth, 1)
    candidates = ordered_moves(state, color, rule)
    if not candidates:
        return SearchResult(-1, -1, -10**9, depth, 0)
    best_move = candidates[0]
    timer = TimeControl(time_limit)
    timer.start()

    for row, col in candidates:
        if timer.expired():
            break
        child = state.copy()
        child.place(row, col, color)
        score, child_nodes = _negamax(child, _opponent(color), depth - 1, -10**9, 10**9, timer, rule)
        score = -score
        nodes += child_nodes + 1
        if score > best_score:
            best_score = score
            best_move = (row, col)

    return SearchResult(best_move[0], best_move[1], best_score, depth, nodes)


def _negamax(
    state: BitboardState,
    color: int,
    depth: int,
    alpha: int,
    beta: int,
    timer: TimeControl,
    rule: str,
) -> tuple[int, int]:
    """Alpha-Beta Negamax 递归。

    当前版本为了先跑通流程，只搜索排序后的前 32 个候选点。真正冲强度时，
    候选点会改成基于邻域、威胁、禁手过滤和开局库的高质量 move ordering。
    """
    if depth <= 0 or timer.expired():
        return evaluate(state, color), 1

    nodes = 1
    best = -10**9
    for row, col in ordered_moves(state, color, rule)[:32]:
        child = state.copy()
        child.place(row, col, color)
        score, child_nodes = _negamax(child, _opponent(color), depth - 1, -beta, -alpha, timer, rule)
        nodes += child_nodes
        score = -score
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best, nodes


def _opponent(color: int) -> int:
    """返回对手颜色。"""
    return WHITE if color == BLACK else BLACK
