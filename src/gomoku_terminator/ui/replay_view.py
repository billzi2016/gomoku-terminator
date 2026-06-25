from __future__ import annotations

from gomoku_terminator.board.bitboard import BLACK, WHITE
from gomoku_terminator.game_session import GameSession
from gomoku_terminator.logging.replay_loader import load_replay
from gomoku_terminator.ui.board_view import SCREEN_SIZE, draw_board

PANEL_HEIGHT = 96
BUTTON_WIDTH = 96
BUTTON_HEIGHT = 34


def run_replay_mode(config) -> int:
    """启动复盘模式。

    后续会加载 JSON log，提供进度条拖拽和相邻的上一步 / 下一步按钮。
    """
    try:
        import pygame
    except ModuleNotFoundError:
        print("Pygame is not installed. Install project dependencies before launching replay UI.")
        return 1

    records = load_replay(config.replay_file)
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE + PANEL_HEIGHT))
    pygame.display.set_caption("Gomoku Terminator Replay")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    step = 0
    prev_button = pygame.Rect(16, SCREEN_SIZE + 50, BUTTON_WIDTH, BUTTON_HEIGHT)
    next_button = pygame.Rect(120, SCREEN_SIZE + 50, BUTTON_WIDTH, BUTTON_HEIGHT)
    slider_rect = pygame.Rect(16, SCREEN_SIZE + 18, SCREEN_SIZE - 32, 14)
    dragging = False
    running = True

    while running:
        session = _session_at(records, step, config.rule)
        draw_board(screen, session.state, config.rule)
        _draw_replay_panel(screen, font, step, len(records), prev_button, next_button, slider_rect, pygame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if prev_button.collidepoint(event.pos):
                    step = max(0, step - 1)
                elif next_button.collidepoint(event.pos):
                    step = min(len(records), step + 1)
                elif slider_rect.collidepoint(event.pos):
                    dragging = True
                    step = _step_from_slider(event.pos[0], slider_rect, len(records))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                step = _step_from_slider(event.pos[0], slider_rect, len(records))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    return 0


def _session_at(records: list[dict], step: int, rule: str) -> GameSession:
    """把复盘日志重建到指定步数。

    复盘不能依赖原对局进程状态，所以每一帧都可以从 log 前 N 手重建 bitboard。
    """

    session = GameSession(rule)
    for record in records[:step]:
        color = BLACK if record["player"] == "black" else WHITE
        session.place(int(record["row"]), int(record["col"]), color)
    return session


def _draw_replay_panel(screen, font, step: int, total: int, prev_button, next_button, slider_rect, pygame) -> None:
    """绘制复盘底部面板。

    上一步和下一步按钮相邻放置，满足 PRD 的交互要求。
    """

    pygame.draw.rect(screen, (232, 218, 190), pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, PANEL_HEIGHT))
    pygame.draw.rect(screen, (180, 170, 150), slider_rect, border_radius=4)
    progress = 0.0 if total == 0 else step / total
    knob_x = slider_rect.left + int(slider_rect.width * progress)
    pygame.draw.circle(screen, (45, 45, 45), (knob_x, slider_rect.centery), 8)
    _draw_button(screen, font, prev_button, "Prev", pygame)
    _draw_button(screen, font, next_button, "Next", pygame)
    label = font.render(f"{step}/{total}", True, (30, 30, 30))
    screen.blit(label, (232, SCREEN_SIZE + 58))


def _draw_button(screen, font, rect, label: str, pygame) -> None:
    """绘制复盘按钮。"""

    pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=4)
    pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=4)
    text = font.render(label, True, (20, 20, 20))
    screen.blit(text, text.get_rect(center=rect.center))


def _step_from_slider(x: int, slider_rect, total: int) -> int:
    """把进度条横坐标转换成复盘步数。"""

    if total <= 0:
        return 0
    ratio = (x - slider_rect.left) / slider_rect.width
    ratio = max(0.0, min(1.0, ratio))
    return int(round(ratio * total))
