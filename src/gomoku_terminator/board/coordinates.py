from __future__ import annotations

BOARD_SIZE = 15
POINT_COUNT = BOARD_SIZE * BOARD_SIZE
BIT_WORDS = 4
BITS_PER_WORD = 64


def validate_row_col(row: int, col: int) -> None:
    """校验二维棋盘坐标。

    本项目统一使用 0-based 坐标：左上角是 `(0, 0)`，右下角是 `(14, 14)`。
    UI、日志、开局库、bitboard 都必须遵守这个约定。
    """
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        raise ValueError(f"row/col out of range: ({row}, {col})")


def row_col_to_index(row: int, col: int) -> int:
    """二维坐标转一维索引。

    15 x 15 棋盘被压平成 0..224。后续 bitboard 会继续把这个 index
    映射到 `uint64[4]` 的某个 word 和 offset。
    """
    validate_row_col(row, col)
    return row * BOARD_SIZE + col


def index_to_row_col(index: int) -> tuple[int, int]:
    """一维索引还原为 `(row, col)`。"""
    if not (0 <= index < POINT_COUNT):
        raise ValueError(f"index out of range: {index}")
    return divmod(index, BOARD_SIZE)


def index_to_word_offset(index: int) -> tuple[int, int]:
    """一维索引转 bitboard 存储位置。

    225 个点需要 225 bit，4 个 uint64 一共 256 bit，足够覆盖整个棋盘。
    """
    if not (0 <= index < POINT_COUNT):
        raise ValueError(f"index out of range: {index}")
    return index // BITS_PER_WORD, index % BITS_PER_WORD


def row_col_to_word_offset(row: int, col: int) -> tuple[int, int]:
    """二维坐标直接转 bitboard 的 `(word, offset)`。"""
    return index_to_word_offset(row_col_to_index(row, col))
