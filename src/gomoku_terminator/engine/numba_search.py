from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import numba as nb
    from numba import prange
except Exception:  # pragma: no cover
    nb = None
    prange = range

BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2
WIN_SCORE = 1_000_000


@dataclass(frozen=True)
class NumbaSearchResult:
    """Numba benchmark 返回结果。"""

    row: int
    col: int
    score: int
    depth: int
    nodes: int
    threads: int


def numba_available() -> bool:
    """当前环境是否可用 Numba。"""

    return nb is not None


def set_numba_threads(threads: int) -> int:
    """设置 Numba 线程数并返回实际线程数。"""

    if nb is None:
        return 1
    nb.set_num_threads(max(1, int(threads)))
    return int(nb.get_num_threads())


def search_empty_benchmark(depth: int, threads: int) -> NumbaSearchResult:
    """兼容旧测试的空棋盘 benchmark。"""

    return search_benchmark(depth=depth, threads=threads, scenario="empty")


def search_benchmark(depth: int, threads: int, scenario: str = "midgame") -> NumbaSearchResult:
    """运行 Numba 根节点并行 benchmark。

    默认使用中盘局面而不是空棋盘。空棋盘只有天元一个根分支，根节点并行没有
    工作量；中盘局面有更多根候选，才能让 24 核更容易跑起来。
    """

    if nb is None:
        raise RuntimeError("Numba is not installed")
    actual_threads = set_numba_threads(threads)
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
    if scenario == "midgame":
        _fill_midgame_board(board)
    row, col, score, nodes = _parallel_root_search(board, BLACK, max(1, int(depth)))
    return NumbaSearchResult(int(row), int(col), int(score), int(depth), int(nodes), actual_threads)


def _fill_midgame_board(board: np.ndarray) -> None:
    """填充一个固定中盘 benchmark 局面。

    这个局面只用于压测搜索，不代表开局库或真实棋谱。它提供足够多的根候选，
    让 `prange` 有分支可分发。
    """

    black = ((7, 7), (7, 8), (8, 7), (6, 8), (8, 9), (5, 6), (9, 8), (6, 6))
    white = ((7, 6), (8, 8), (6, 7), (9, 7), (5, 8), (8, 5), (9, 9))
    for row, col in black:
        board[row, col] = BLACK
    for row, col in white:
        board[row, col] = WHITE


if nb is not None:

    @nb.njit(cache=False)
    def _winner_from(board: np.ndarray, row: int, col: int, color: int) -> bool:
        dirs = ((0, 1), (1, 0), (1, 1), (1, -1))
        for k in range(4):
            dr = dirs[k][0]
            dc = dirs[k][1]
            total = 1
            r = row + dr
            c = col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r, c] == color:
                total += 1
                r += dr
                c += dc
            r = row - dr
            c = col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r, c] == color:
                total += 1
                r -= dr
                c -= dc
            if total >= 5:
                return True
        return False

    @nb.njit(cache=False)
    def _line_score(length: int, open_ends: int) -> int:
        if length >= 5:
            return WIN_SCORE
        if length == 4 and open_ends == 2:
            return 120_000
        if length == 4 and open_ends == 1:
            return 25_000
        if length == 3 and open_ends == 2:
            return 8_000
        if length == 3 and open_ends == 1:
            return 1_200
        if length == 2 and open_ends == 2:
            return 400
        if length == 2 and open_ends == 1:
            return 80
        return 0

    @nb.njit(cache=False)
    def _evaluate_color(board: np.ndarray, color: int) -> int:
        score = 0
        dirs = ((0, 1), (1, 0), (1, 1), (1, -1))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row, col] != color:
                    continue
                center_dist = abs(row - 7) + abs(col - 7)
                score += 3
                if center_dist < 14:
                    score += 14 - center_dist
                for k in range(4):
                    dr = dirs[k][0]
                    dc = dirs[k][1]
                    prev_r = row - dr
                    prev_c = col - dc
                    if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE and board[prev_r, prev_c] == color:
                        continue
                    length = 1
                    r = row + dr
                    c = col + dc
                    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r, c] == color:
                        length += 1
                        r += dr
                        c += dc
                    open_ends = 0
                    if 0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE and board[prev_r, prev_c] == EMPTY:
                        open_ends += 1
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r, c] == EMPTY:
                        open_ends += 1
                    score += _line_score(length, open_ends)
        return score

    @nb.njit(cache=False)
    def _evaluate(board: np.ndarray, color: int) -> int:
        opponent = WHITE if color == BLACK else BLACK
        return _evaluate_color(board, color) - _evaluate_color(board, opponent)

    @nb.njit(cache=False)
    def _generate_moves(board: np.ndarray, moves: np.ndarray) -> int:
        occupied = 0
        marker = np.zeros(BOARD_SIZE * BOARD_SIZE, dtype=np.int8)
        count = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row, col] == EMPTY:
                    continue
                occupied += 1
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if dr == 0 and dc == 0:
                            continue
                        r = row + dr
                        c = col + dc
                        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                            if board[r, c] == EMPTY:
                                index = r * BOARD_SIZE + c
                                if marker[index] == 0:
                                    marker[index] = 1
                                    moves[count] = index
                                    count += 1
        if occupied == 0:
            moves[0] = 7 * BOARD_SIZE + 7
            return 1
        return count

    @nb.njit(cache=False)
    def _negamax_numba(board: np.ndarray, color: int, depth: int, alpha: int, beta: int) -> tuple[int, int]:
        if depth <= 0:
            return _evaluate(board, color), 1

        moves = np.empty(BOARD_SIZE * BOARD_SIZE, dtype=np.int16)
        count = _generate_moves(board, moves)
        if count == 0:
            return _evaluate(board, color), 1

        opponent = WHITE if color == BLACK else BLACK
        best = -1_000_000_000
        nodes = 1
        for i in range(count):
            index = int(moves[i])
            row = index // BOARD_SIZE
            col = index - row * BOARD_SIZE
            board[row, col] = color
            if _winner_from(board, row, col, color):
                score = WIN_SCORE
                child_nodes = 1
            else:
                child_score, child_nodes = _negamax_numba(board, opponent, depth - 1, -beta, -alpha)
                score = -child_score
            board[row, col] = EMPTY
            nodes += child_nodes
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best, nodes

    @nb.njit(parallel=True, cache=False)
    def _parallel_root_search(board: np.ndarray, color: int, depth: int) -> tuple[int, int, int, int]:
        root_moves = np.empty(BOARD_SIZE * BOARD_SIZE, dtype=np.int16)
        root_count = _generate_moves(board, root_moves)
        scores = np.empty(root_count, dtype=np.int64)
        nodes = np.empty(root_count, dtype=np.int64)
        opponent = WHITE if color == BLACK else BLACK

        for i in prange(root_count):
            local = board.copy()
            index = int(root_moves[i])
            row = index // BOARD_SIZE
            col = index - row * BOARD_SIZE
            local[row, col] = color
            if _winner_from(local, row, col, color):
                scores[i] = WIN_SCORE
                nodes[i] = 1
            else:
                score, child_nodes = _negamax_numba(local, opponent, depth - 1, -1_000_000_000, 1_000_000_000)
                scores[i] = -score
                nodes[i] = child_nodes + 1

        best_i = 0
        best_score = scores[0]
        total_nodes = 0
        for i in range(root_count):
            total_nodes += int(nodes[i])
            if scores[i] > best_score:
                best_score = scores[i]
                best_i = i
        best_index = int(root_moves[best_i])
        return best_index // BOARD_SIZE, best_index % BOARD_SIZE, int(best_score), int(total_nodes)
