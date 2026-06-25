from __future__ import annotations

import random

from gomoku_terminator.board.coordinates import POINT_COUNT

BLACK_PLANE = 0
WHITE_PLANE = 1


def build_zobrist_table(seed: int = 20260624) -> list[list[int]]:
    """生成 Zobrist 哈希表。

    Zobrist 用于把棋盘局面压成 64 位 key，后续置换表靠它快速判断“这个局面
    是否搜过”。固定 seed 可以保证测试和复盘时哈希稳定。
    """
    rng = random.Random(seed)
    return [[rng.getrandbits(64) for _ in range(POINT_COUNT)] for _ in range(2)]


def hash_moves(moves: list[tuple[int, int, int]], table: list[list[int]] | None = None) -> int:
    """根据落子序列计算哈希。

    当前是工具版实现；正式搜索会直接基于 bitboard 增量更新哈希，减少重复计算。
    """
    from gomoku_terminator.board.bitboard import BLACK
    from gomoku_terminator.board.coordinates import row_col_to_index

    table = build_zobrist_table() if table is None else table
    value = 0
    for row, col, color in moves:
        plane = BLACK_PLANE if color == BLACK else WHITE_PLANE
        value ^= table[plane][row_col_to_index(row, col)]
    return value
