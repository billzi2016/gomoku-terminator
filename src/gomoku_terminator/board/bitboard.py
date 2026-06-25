from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from gomoku_terminator.board.coordinates import (
    BIT_WORDS,
    BOARD_SIZE,
    POINT_COUNT,
    index_to_row_col,
    index_to_word_offset,
    row_col_to_index,
)

EMPTY = 0
BLACK = 1
WHITE = 2


def _empty_bits() -> np.ndarray:
    """创建一方棋子的空 bitboard。"""
    return np.zeros(BIT_WORDS, dtype=np.uint64)


def _mask(index: int) -> tuple[int, np.uint64]:
    """生成指定棋盘点对应的 word 下标和 bit mask。"""
    word, offset = index_to_word_offset(index)
    return word, np.uint64(1) << np.uint64(offset)


@dataclass
class BitboardState:
    """棋盘真源状态。

    UI 可以把它转换成矩阵来画，但搜索、规则、日志重建都应该以这个结构为准。
    当前版本用 NumPy `uint64[4]` 表示黑白双方，后续 Numba 热点函数也会围绕
    这个布局优化。
    """
    black: np.ndarray = field(default_factory=_empty_bits)
    white: np.ndarray = field(default_factory=_empty_bits)
    side_to_move: int = BLACK

    def copy(self) -> "BitboardState":
        """复制棋盘。

        4 个 uint64 只有 32 字节，一次搜索分支复制成本很低；比复制二维 list
        更适合后续暴力搜索。
        """
        return BitboardState(self.black.copy(), self.white.copy(), self.side_to_move)

    def occupied_at_index(self, index: int) -> bool:
        """判断某个一维点是否已被黑棋或白棋占用。"""
        word, mask = _mask(index)
        return bool((self.black[word] | self.white[word]) & mask)

    def color_at_index(self, index: int) -> int:
        """读取一维点颜色，返回 EMPTY / BLACK / WHITE。"""
        word, mask = _mask(index)
        if self.black[word] & mask:
            return BLACK
        if self.white[word] & mask:
            return WHITE
        return EMPTY

    def color_at(self, row: int, col: int) -> int:
        """读取二维坐标颜色。"""
        return self.color_at_index(row_col_to_index(row, col))

    def is_empty_at(self, row: int, col: int) -> bool:
        """判断二维坐标是否为空。"""
        return self.color_at(row, col) == EMPTY

    def place(self, row: int, col: int, color: int | None = None) -> None:
        """落子。

        这里故意在底层抛出重复落子的错误，避免 UI 或 AI 返回非法点时悄悄覆盖。
        Renju 禁手不在本函数判断，而是在规则层和候选点生成阶段处理。
        """
        color = self.side_to_move if color is None else color
        if color not in (BLACK, WHITE):
            raise ValueError(f"invalid color: {color}")

        index = row_col_to_index(row, col)
        if self.occupied_at_index(index):
            raise ValueError(f"point already occupied: ({row}, {col})")

        word, mask = _mask(index)
        if color == BLACK:
            self.black[word] |= mask
            self.side_to_move = WHITE
        else:
            self.white[word] |= mask
            self.side_to_move = BLACK

    def remove(self, row: int, col: int) -> None:
        """移除一个点上的棋子。

        主要服务于悔棋、复盘跳转和后续搜索临时回滚。
        """
        index = row_col_to_index(row, col)
        word, mask = _mask(index)
        inv = ~mask
        self.black[word] &= inv
        self.white[word] &= inv

    def legal_empty_points(self) -> list[tuple[int, int]]:
        """返回当前所有空点。

        这是清晰版实现；正式搜索会改成邻域候选点生成，避免 225 点全扫。
        """
        points: list[tuple[int, int]] = []
        for index in range(POINT_COUNT):
            if not self.occupied_at_index(index):
                points.append(index_to_row_col(index))
        return points

    def to_matrix(self) -> list[list[int]]:
        """转换成 UI 友好的二维矩阵快照。"""
        matrix = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for index in range(POINT_COUNT):
            row, col = index_to_row_col(index)
            matrix[row][col] = self.color_at_index(index)
        return matrix

    @classmethod
    def from_moves(cls, moves: list[tuple[int, int]], first: int = BLACK) -> "BitboardState":
        """从落子序列重建棋盘。

        复盘模块会频繁需要“播放到第 N 手”的状态重建，这个函数就是基础能力。
        """
        state = cls(side_to_move=first)
        color = first
        for row, col in moves:
            state.place(row, col, color)
            color = WHITE if color == BLACK else BLACK
            state.side_to_move = color
        return state
