from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.ui.forbidden_overlay import current_forbidden_points

GRID_SIZE = 40
BOARD_SIZE = 15
MARGIN = 40
SCREEN_SIZE = GRID_SIZE * (BOARD_SIZE - 1) + MARGIN * 2

COLOR_WOOD = (245, 210, 155)
COLOR_LINE = (40, 40, 40)
COLOR_BLACK = (10, 10, 10)
COLOR_WHITE = (245, 245, 245)
COLOR_WHITE_EDGE = (200, 200, 200)
COLOR_FORBIDDEN = (210, 32, 32)


def get_board_coords(mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
    """把鼠标像素坐标映射到棋盘交叉点。

    Pygame 鼠标事件给的是屏幕像素，搜索和规则需要的是 `(row, col)`。
    这里用 round 贴近最近交叉点，点击棋盘外则返回 None。
    """
    x, y = mouse_pos
    col = round((x - MARGIN) / GRID_SIZE)
    row = round((y - MARGIN) / GRID_SIZE)
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None


def draw_board(
    screen,
    state: BitboardState,
    rule: str = "renju",
    forbidden_cache: list[tuple[int, int]] | None = None,
) -> None:
    """绘制棋盘、棋子和黑棋禁手红色 X。

    这个函数只负责可视化，不决定规则真假。红色 X 的数据来自
    `rules/renju_forbidden.py`，保证人机、机机和复盘看到的是同一套禁手结果。
    UI 实战中会传入缓存，避免每一帧都全盘重算禁手导致鼠标点击后卡顿。
    """
    import pygame

    screen.fill(COLOR_WOOD)
    for i in range(BOARD_SIZE):
        pygame.draw.line(
            screen,
            COLOR_LINE,
            (MARGIN, MARGIN + i * GRID_SIZE),
            (SCREEN_SIZE - MARGIN, MARGIN + i * GRID_SIZE),
            2,
        )
        pygame.draw.line(
            screen,
            COLOR_LINE,
            (MARGIN + i * GRID_SIZE, MARGIN),
            (MARGIN + i * GRID_SIZE, SCREEN_SIZE - MARGIN),
            2,
        )

    for row, col in ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11)):
        pygame.draw.circle(screen, COLOR_LINE, _pixel(row, col), 5)

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = state.color_at(row, col)
            if color == BLACK:
                pygame.draw.circle(screen, COLOR_BLACK, _pixel(row, col), GRID_SIZE // 2 - 2)
            elif color == WHITE:
                pygame.draw.circle(screen, COLOR_WHITE, _pixel(row, col), GRID_SIZE // 2 - 2)
                pygame.draw.circle(screen, COLOR_WHITE_EDGE, _pixel(row, col), GRID_SIZE // 2 - 2, 1)

    forbidden_points = current_forbidden_points(state, rule) if forbidden_cache is None else forbidden_cache
    for row, col in forbidden_points:
        x, y = _pixel(row, col)
        delta = GRID_SIZE // 4
        pygame.draw.line(screen, COLOR_FORBIDDEN, (x - delta, y - delta), (x + delta, y + delta), 3)
        pygame.draw.line(screen, COLOR_FORBIDDEN, (x + delta, y - delta), (x - delta, y + delta), 3)


def _pixel(row: int, col: int) -> tuple[int, int]:
    """棋盘坐标转像素坐标。"""
    return MARGIN + col * GRID_SIZE, MARGIN + row * GRID_SIZE
