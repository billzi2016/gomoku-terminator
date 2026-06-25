from __future__ import annotations

from gomoku_terminator.board.coordinates import BOARD_SIZE


def transform_point(row: int, col: int, transform: str) -> tuple[int, int]:
    """对单个坐标执行棋盘对称变换。

    开局库必须支持旋转和翻转，否则同一个职业开局换个方向就无法命中。
    """
    last = BOARD_SIZE - 1
    if transform == "identity":
        return row, col
    if transform == "rot90":
        return col, last - row
    if transform == "rot180":
        return last - row, last - col
    if transform == "rot270":
        return last - col, row
    if transform == "flip_h":
        return row, last - col
    if transform == "flip_v":
        return last - row, col
    if transform == "diag_main":
        return col, row
    if transform == "diag_anti":
        return last - col, last - row
    raise ValueError(f"unknown transform: {transform}")


def all_transforms(row: int, col: int) -> dict[str, tuple[int, int]]:
    """返回一个坐标的 8 种对称结果。"""
    return {
        name: transform_point(row, col, name)
        for name in (
            "identity",
            "rot90",
            "rot180",
            "rot270",
            "flip_h",
            "flip_v",
            "diag_main",
            "diag_anti",
        )
    }
