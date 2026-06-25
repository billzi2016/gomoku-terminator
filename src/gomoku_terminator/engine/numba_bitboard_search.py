from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

try:
    import numba as nb
    from numba import prange
except Exception:  # pragma: no cover
    nb = None
    prange = range

BOARD_SIZE = 15
POINT_COUNT = 225
BIT_WORDS = 4
BLACK = 1
WHITE = 2
WIN_SCORE = 1_000_000
ROOT_MOVE_LIMIT = 40
DEEP_MOVE_LIMIT = 18
SHALLOW_MOVE_LIMIT = 12
EXTREME_ROOT_MOVE_LIMIT = 32
EXTREME_DEEP_MOVE_LIMIT = 8
EXTREME_MID_MOVE_LIMIT = 12
EXTREME_SHALLOW_MOVE_LIMIT = 16


@dataclass(frozen=True)
class BitboardBenchmarkResult:
    """4xuint64 benchmark 结果。

    这是独立极限版入口，不替代 Python 可读版和 Numba 矩阵版。
    """

    occupied: int
    win: bool


@dataclass(frozen=True)
class BitboardSearchResult:
    """4xuint64 搜索 benchmark 结果。"""

    row: int
    col: int
    score: int
    depth: int
    nodes: int
    threads: int


def bitboard_backend_available() -> bool:
    """当前环境是否可运行 Numba bitboard 后端。"""

    return nb is not None


def run_bitboard_smoke() -> BitboardBenchmarkResult:
    """4xuint64 后端 smoke test。

    第一阶段只验证 Numba 可以操作 `uint64[4]`、设置 bit、统计占用和检查五连。
    搜索递归会在这个独立模块里继续推进，不污染现有后端。
    """

    if nb is None:
        raise RuntimeError("Numba is not installed")
    black = np.zeros(BIT_WORDS, dtype=np.uint64)
    white = np.zeros(BIT_WORDS, dtype=np.uint64)
    for col in range(5):
        _set_bit(black, 7 * BOARD_SIZE + col)
    occupied = _occupied_count(black, white)
    win = _has_five(black)
    return BitboardBenchmarkResult(int(occupied), bool(win))


def run_bitboard_benchmark(depth: int, threads: int, scenario: str = "midgame") -> BitboardSearchResult:
    """运行 4xuint64 Numba 搜索 benchmark。

    这是第三后端的真正可执行入口。它不替代可读 Python 版，也不替代矩阵 Numba
    中间版；它用于验证极限 bitboard 表示能实际搜索并输出 NPS。
    """

    if nb is None:
        raise RuntimeError("Numba is not installed")
    nb.set_num_threads(max(1, int(threads)))
    black = np.zeros(BIT_WORDS, dtype=np.uint64)
    white = np.zeros(BIT_WORDS, dtype=np.uint64)
    if scenario == "midgame":
        _fill_midgame_bits(black, white)
    row, col, score, nodes = _parallel_root_search_bits(black, white, BLACK, max(1, int(depth)))
    return BitboardSearchResult(int(row), int(col), int(score), int(depth), int(nodes), int(nb.get_num_threads()))


def search_bitboard_arrays(
    black: np.ndarray,
    white: np.ndarray,
    color: int,
    depth: int,
    threads: int,
) -> BitboardSearchResult:
    """从当前 4xuint64 棋盘搜索最佳点。

    UI / selfplay 会通过这个入口使用最高效的 bitboard 后端。传入数组会复制，
    不会修改 Python 可读棋盘真源。
    """

    if nb is None:
        raise RuntimeError("Numba is not installed")
    nb.set_num_threads(max(1, int(threads)))
    black_bits = black.astype(np.uint64, copy=True)
    white_bits = white.astype(np.uint64, copy=True)
    row, col, score, nodes = _parallel_root_search_bits(black_bits, white_bits, int(color), max(1, int(depth)))
    return BitboardSearchResult(int(row), int(col), int(score), int(depth), int(nodes), int(nb.get_num_threads()))


def search_bitboard_arrays_extreme(
    black: np.ndarray,
    white: np.ndarray,
    color: int,
    depth: int,
    threads: int,
    time_limit: float,
) -> BitboardSearchResult:
    """freestyle 极限模式入口：迭代加深到目标层数。

    Numba 递归内目前还不能被 Python 定时器抢占，所以这里不直接一口气硬搜
    16/20 层，而是从浅层逐步加深。每完成一层就保留完整结果；如果剩余时间
    不足以支撑下一层，就返回上一层的稳定答案。
    """

    if nb is None:
        raise RuntimeError("Numba is not installed")
    nb.set_num_threads(max(1, int(threads)))
    target_depth = max(1, int(depth))
    deadline = time.perf_counter() + max(0.001, float(time_limit))
    best: BitboardSearchResult | None = None
    total_nodes = 0
    last_elapsed = 0.0

    for current_depth in range(1, target_depth + 1):
        now = time.perf_counter()
        if best is not None and now >= deadline:
            break
        remaining = deadline - now
        if best is not None and last_elapsed > 0 and remaining < last_elapsed * 1.8:
            break

        black_bits = black.astype(np.uint64, copy=True)
        white_bits = white.astype(np.uint64, copy=True)
        started = time.perf_counter()
        row, col, score, nodes = _parallel_root_search_bits_extreme(black_bits, white_bits, int(color), current_depth)
        last_elapsed = time.perf_counter() - started
        total_nodes += int(nodes)
        best = BitboardSearchResult(
            int(row),
            int(col),
            int(score),
            int(current_depth),
            int(total_nodes),
            int(nb.get_num_threads()),
        )
        if abs(int(score)) >= WIN_SCORE:
            break

    if best is None:
        return search_bitboard_arrays(black, white, color, 1, threads)
    return best


def _fill_midgame_bits(black: np.ndarray, white: np.ndarray) -> None:
    """填充和矩阵 Numba 相同风格的中盘压测局面。"""

    black_points = ((7, 7), (7, 8), (8, 7), (6, 8), (8, 9), (5, 6), (9, 8), (6, 6))
    white_points = ((7, 6), (8, 8), (6, 7), (9, 7), (5, 8), (8, 5), (9, 9))
    for row, col in black_points:
        _set_bit(black, row * BOARD_SIZE + col)
    for row, col in white_points:
        _set_bit(white, row * BOARD_SIZE + col)


if nb is not None:

    @nb.njit(cache=False)
    def _word(index: int) -> int:
        return index // 64

    @nb.njit(cache=False)
    def _offset(index: int) -> int:
        return index - (index // 64) * 64

    @nb.njit(cache=False)
    def _mask(index: int) -> np.uint64:
        return np.uint64(1) << np.uint64(_offset(index))

    @nb.njit(cache=False)
    def _set_bit(bits: np.ndarray, index: int) -> None:
        bits[_word(index)] = bits[_word(index)] | _mask(index)

    @nb.njit(cache=False)
    def _clear_bit(bits: np.ndarray, index: int) -> None:
        bits[_word(index)] = bits[_word(index)] & ~_mask(index)

    @nb.njit(cache=False)
    def _has_bit(bits: np.ndarray, index: int) -> bool:
        return (bits[_word(index)] & _mask(index)) != 0

    @nb.njit(cache=False)
    def _occupied_count(black: np.ndarray, white: np.ndarray) -> int:
        total = 0
        for index in range(POINT_COUNT):
            if _has_bit(black, index) or _has_bit(white, index):
                total += 1
        return total

    @nb.njit(cache=False)
    def _is_empty(black: np.ndarray, white: np.ndarray, index: int) -> bool:
        return not _has_bit(black, index) and not _has_bit(white, index)

    @nb.njit(cache=False)
    def _place(black: np.ndarray, white: np.ndarray, index: int, color: int) -> None:
        if color == BLACK:
            _set_bit(black, index)
        else:
            _set_bit(white, index)

    @nb.njit(cache=False)
    def _remove(black: np.ndarray, white: np.ndarray, index: int, color: int) -> None:
        if color == BLACK:
            _clear_bit(black, index)
        else:
            _clear_bit(white, index)

    @nb.njit(cache=False)
    def _has_five(bits: np.ndarray) -> bool:
        dirs = (1, 15, 16, 14)
        for index in range(POINT_COUNT):
            if not _has_bit(bits, index):
                continue
            row = index // BOARD_SIZE
            col = index - row * BOARD_SIZE
            for k in range(4):
                step = dirs[k]
                count = 1
                current = index + step
                while 0 <= current < POINT_COUNT and _same_line(index, current, step):
                    if not _has_bit(bits, current):
                        break
                    count += 1
                    current += step
                if count >= 5:
                    return True
        return False

    @nb.njit(cache=False)
    def _has_five_from(bits: np.ndarray, row: int, col: int) -> bool:
        dirs = ((0, 1), (1, 0), (1, 1), (1, -1))
        for k in range(4):
            dr = dirs[k][0]
            dc = dirs[k][1]
            total = 1
            r = row + dr
            c = col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if not _has_bit(bits, r * BOARD_SIZE + c):
                    break
                total += 1
                r += dr
                c += dc
            r = row - dr
            c = col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if not _has_bit(bits, r * BOARD_SIZE + c):
                    break
                total += 1
                r -= dr
                c -= dc
            if total >= 5:
                return True
        return False

    @nb.njit(cache=False)
    def _same_line(start: int, current: int, step: int) -> bool:
        start_row = start // BOARD_SIZE
        start_col = start - start_row * BOARD_SIZE
        row = current // BOARD_SIZE
        col = current - row * BOARD_SIZE
        if step == 1:
            return row == start_row
        if step == 15:
            return col == start_col
        if step == 16:
            return row - start_row == col - start_col
        if step == 14:
            return row - start_row == start_col - col
        return False

    @nb.njit(cache=False)
    def _generate_moves_bits(black: np.ndarray, white: np.ndarray, color: int, moves: np.ndarray) -> int:
        marker = np.zeros(POINT_COUNT, dtype=np.int8)
        occupied = 0
        count = 0
        for index in range(POINT_COUNT):
            if _is_empty(black, white, index):
                continue
            occupied += 1
            row = index // BOARD_SIZE
            col = index - row * BOARD_SIZE
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    if dr == 0 and dc == 0:
                        continue
                    r = row + dr
                    c = col + dc
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                        move = r * BOARD_SIZE + c
                        if marker[move] == 0 and _is_empty(black, white, move):
                            marker[move] = 1
                            moves[count] = move
                            count += 1
        if occupied == 0:
            moves[0] = 7 * BOARD_SIZE + 7
            return 1
        _sort_moves_bits(black, white, color, moves, count)
        return count

    @nb.njit(cache=False)
    def _limit_for_depth(depth: int, is_root: bool) -> int:
        """按层数收紧候选数。

        越深的递归越容易发生组合爆炸，因此只保留战术评分最高的一小批点。
        root 层保留更多选择，避免 UI 里明显漏招；内部层更激进，让 Alpha-Beta
        可以快速把坏分支剪掉。
        """

        if is_root:
            return ROOT_MOVE_LIMIT
        if depth >= 4:
            return DEEP_MOVE_LIMIT
        return SHALLOW_MOVE_LIMIT

    @nb.njit(cache=False)
    def _extreme_limit_for_depth(depth: int, is_root: bool) -> int:
        """extreme 专用候选限制。

        16 层要能落地，必须比 mild 更重视强制手和排序结果。root 保留足够选择，
        深层则只保留最高价值威胁点，让迭代加深尽可能完成更深层。
        """

        if is_root:
            return EXTREME_ROOT_MOVE_LIMIT
        if depth >= 8:
            return EXTREME_DEEP_MOVE_LIMIT
        if depth >= 4:
            return EXTREME_MID_MOVE_LIMIT
        return EXTREME_SHALLOW_MOVE_LIMIT

    @nb.njit(cache=False)
    def _sort_moves_bits(
        black: np.ndarray,
        white: np.ndarray,
        color: int,
        moves: np.ndarray,
        count: int,
    ) -> None:
        """按战术价值原地排序候选点。

        Numba 递归里避免 Python 对象和 list sort，这里用简单选择排序。候选已经
        经过邻域过滤，数量通常不大；排序成本远小于错误顺序造成的搜索爆炸。
        """

        scores = np.empty(POINT_COUNT, dtype=np.int64)
        for i in range(count):
            scores[i] = _move_score_bits(black, white, int(moves[i]), color)

        for i in range(count - 1):
            best_i = i
            best_score = scores[i]
            for j in range(i + 1, count):
                if scores[j] > best_score:
                    best_score = scores[j]
                    best_i = j
            if best_i != i:
                tmp_move = moves[i]
                moves[i] = moves[best_i]
                moves[best_i] = tmp_move
                tmp_score = scores[i]
                scores[i] = scores[best_i]
                scores[best_i] = tmp_score

    @nb.njit(cache=False)
    def _move_score_bits(black: np.ndarray, white: np.ndarray, move: int, color: int) -> int:
        """候选点战术打分。

        评分只看一步后的局部线型：自己立刻成五最高，其次堵对方成五，再看活四、
        冲四、活三等棋形。这个函数不追求完整评估，只负责让搜索先看强制手。
        """

        row = move // BOARD_SIZE
        col = move - row * BOARD_SIZE
        own = black if color == BLACK else white
        opp = white if color == BLACK else black
        opponent = WHITE if color == BLACK else BLACK

        _place(black, white, move, color)
        if _has_five_from(own, row, col):
            _remove(black, white, move, color)
            return WIN_SCORE * 10
        own_score = _local_shape_score_bits(black, white, row, col, color)
        _remove(black, white, move, color)

        _place(black, white, move, opponent)
        if _has_five_from(opp, row, col):
            _remove(black, white, move, opponent)
            return WIN_SCORE * 9
        block_score = _local_shape_score_bits(black, white, row, col, opponent)
        _remove(black, white, move, opponent)

        center = BOARD_SIZE // 2
        center_score = 30 - (abs(row - center) + abs(col - center))
        return own_score + block_score // 2 + center_score

    @nb.njit(cache=False)
    def _local_shape_score_bits(black: np.ndarray, white: np.ndarray, row: int, col: int, color: int) -> int:
        bits = black if color == BLACK else white
        best = 0
        dirs = ((0, 1), (1, 0), (1, 1), (1, -1))
        for k in range(4):
            dr = dirs[k][0]
            dc = dirs[k][1]
            length = 1
            open_ends = 0

            r = row + dr
            c = col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if not _has_bit(bits, r * BOARD_SIZE + c):
                    break
                length += 1
                r += dr
                c += dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and _is_empty(black, white, r * BOARD_SIZE + c):
                open_ends += 1

            r = row - dr
            c = col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if not _has_bit(bits, r * BOARD_SIZE + c):
                    break
                length += 1
                r -= dr
                c -= dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and _is_empty(black, white, r * BOARD_SIZE + c):
                open_ends += 1

            score = _shape_value_bits(length, open_ends)
            if score > best:
                best = score
        return best

    @nb.njit(cache=False)
    def _shape_value_bits(length: int, open_ends: int) -> int:
        if length >= 5:
            return WIN_SCORE
        if length == 4 and open_ends == 2:
            return 300_000
        if length == 4 and open_ends == 1:
            return 90_000
        if length == 3 and open_ends == 2:
            return 35_000
        if length == 3 and open_ends == 1:
            return 6_000
        if length == 2 and open_ends == 2:
            return 1_200
        if length == 2 and open_ends == 1:
            return 180
        return 0

    @nb.njit(cache=False)
    def _evaluate_bits(black: np.ndarray, white: np.ndarray, color: int) -> int:
        own = black if color == BLACK else white
        opp = white if color == BLACK else black
        return _evaluate_one(own) - _evaluate_one(opp)

    @nb.njit(cache=False)
    def _evaluate_one(bits: np.ndarray) -> int:
        score = 0
        center = 7
        for index in range(POINT_COUNT):
            if not _has_bit(bits, index):
                continue
            row = index // BOARD_SIZE
            col = index - row * BOARD_SIZE
            dist = abs(row - center) + abs(col - center)
            if dist < 14:
                score += 14 - dist
            score += 3
        if _has_five(bits):
            score += WIN_SCORE
        return score

    @nb.njit(cache=False)
    def _negamax_bits(
        black: np.ndarray,
        white: np.ndarray,
        color: int,
        depth: int,
        alpha: int,
        beta: int,
    ) -> tuple[int, int]:
        if depth <= 0:
            return _evaluate_bits(black, white, color), 1

        moves = np.empty(POINT_COUNT, dtype=np.int16)
        count = _generate_moves_bits(black, white, color, moves)
        if count == 0:
            return _evaluate_bits(black, white, color), 1
        limit = _limit_for_depth(depth, False)
        if count > limit:
            count = limit

        opponent = WHITE if color == BLACK else BLACK
        own = black if color == BLACK else white
        best = -1_000_000_000
        nodes = 1
        for i in range(count):
            move = int(moves[i])
            row = move // BOARD_SIZE
            col = move - row * BOARD_SIZE
            _place(black, white, move, color)
            if _has_five_from(own, row, col):
                score = WIN_SCORE
                child_nodes = 1
            else:
                child_score, child_nodes = _negamax_bits(black, white, opponent, depth - 1, -beta, -alpha)
                score = -child_score
            _remove(black, white, move, color)
            nodes += child_nodes
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best, nodes

    @nb.njit(cache=False)
    def _negamax_bits_extreme(
        black: np.ndarray,
        white: np.ndarray,
        color: int,
        depth: int,
        alpha: int,
        beta: int,
    ) -> tuple[int, int]:
        if depth <= 0:
            return _evaluate_bits(black, white, color), 1

        moves = np.empty(POINT_COUNT, dtype=np.int16)
        count = _generate_moves_bits(black, white, color, moves)
        if count == 0:
            return _evaluate_bits(black, white, color), 1
        limit = _extreme_limit_for_depth(depth, False)
        if count > limit:
            count = limit

        opponent = WHITE if color == BLACK else BLACK
        own = black if color == BLACK else white
        best = -1_000_000_000
        nodes = 1
        for i in range(count):
            move = int(moves[i])
            row = move // BOARD_SIZE
            col = move - row * BOARD_SIZE
            _place(black, white, move, color)
            if _has_five_from(own, row, col):
                score = WIN_SCORE
                child_nodes = 1
            else:
                child_score, child_nodes = _negamax_bits_extreme(black, white, opponent, depth - 1, -beta, -alpha)
                score = -child_score
            _remove(black, white, move, color)
            nodes += child_nodes
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best, nodes

    @nb.njit(parallel=True, cache=False)
    def _parallel_root_search_bits(
        black: np.ndarray,
        white: np.ndarray,
        color: int,
        depth: int,
    ) -> tuple[int, int, int, int]:
        root_moves = np.empty(POINT_COUNT, dtype=np.int16)
        root_count = _generate_moves_bits(black, white, color, root_moves)
        root_limit = _limit_for_depth(depth, True)
        if root_count > root_limit:
            root_count = root_limit
        scores = np.empty(root_count, dtype=np.int64)
        nodes = np.empty(root_count, dtype=np.int64)
        opponent = WHITE if color == BLACK else BLACK

        for i in prange(root_count):
            local_black = black.copy()
            local_white = white.copy()
            move = int(root_moves[i])
            row = move // BOARD_SIZE
            col = move - row * BOARD_SIZE
            _place(local_black, local_white, move, color)
            own = local_black if color == BLACK else local_white
            if _has_five_from(own, row, col):
                scores[i] = WIN_SCORE
                nodes[i] = 1
            else:
                score, child_nodes = _negamax_bits(
                    local_black,
                    local_white,
                    opponent,
                    depth - 1,
                    -1_000_000_000,
                    1_000_000_000,
                )
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

    @nb.njit(parallel=True, cache=False)
    def _parallel_root_search_bits_extreme(
        black: np.ndarray,
        white: np.ndarray,
        color: int,
        depth: int,
    ) -> tuple[int, int, int, int]:
        root_moves = np.empty(POINT_COUNT, dtype=np.int16)
        root_count = _generate_moves_bits(black, white, color, root_moves)
        root_limit = _extreme_limit_for_depth(depth, True)
        if root_count > root_limit:
            root_count = root_limit
        scores = np.empty(root_count, dtype=np.int64)
        nodes = np.empty(root_count, dtype=np.int64)
        opponent = WHITE if color == BLACK else BLACK

        for i in prange(root_count):
            local_black = black.copy()
            local_white = white.copy()
            move = int(root_moves[i])
            row = move // BOARD_SIZE
            col = move - row * BOARD_SIZE
            _place(local_black, local_white, move, color)
            own = local_black if color == BLACK else local_white
            if _has_five_from(own, row, col):
                scores[i] = WIN_SCORE
                nodes[i] = 1
            else:
                score, child_nodes = _negamax_bits_extreme(
                    local_black,
                    local_white,
                    opponent,
                    depth - 1,
                    -1_000_000_000,
                    1_000_000_000,
                )
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
