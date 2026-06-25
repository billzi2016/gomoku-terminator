from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import numba as nb
except Exception:  # pragma: no cover
    nb = None

BOARD_SIZE = 15
POINT_COUNT = 225
BIT_WORDS = 4
BLACK = 1
WHITE = 2


@dataclass(frozen=True)
class BitboardBenchmarkResult:
    """4xuint64 benchmark 结果。

    这是独立极限版入口，不替代 Python 可读版和 Numba 矩阵版。
    """

    occupied: int
    win: bool


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
