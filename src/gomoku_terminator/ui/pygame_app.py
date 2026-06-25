from __future__ import annotations

from pathlib import Path
import time
from uuid import uuid4

from gomoku_terminator.board.bitboard import BLACK, WHITE
from gomoku_terminator.board.coordinates import row_col_to_index
from gomoku_terminator.game_session import GameSession, color_name
from gomoku_terminator.logging.game_log import GameLogWriter, MoveLog
from gomoku_terminator.rules.renju_forbidden import forbidden_points
from gomoku_terminator.ui.forbidden_overlay import ForbiddenOverlayWorker
from gomoku_terminator.ui.ai_worker import AIWorker
from gomoku_terminator.ui.ai_worker import _search_with_engine
from gomoku_terminator.ui.board_view import SCREEN_SIZE, draw_board, get_board_coords

PANEL_HEIGHT = 88
STATS_WIDTH = 320
BUTTON_HEIGHT = 34
BUTTON_WIDTH = 96
AI_DEPTH = 2


def _opponent(color: int) -> int:
    """返回对手颜色。"""

    return WHITE if color == BLACK else BLACK


def run_play_mode(config) -> int:
    """启动人机模式。

    当前是可运行骨架；下一步会接入真正的棋盘窗口、鼠标落子、红色禁手 X、
    AI worker 和悔棋一步。
    """
    try:
        import pygame
    except ModuleNotFoundError:
        print("Pygame is not installed. Install project dependencies before launching UI.")
        return 1

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE + STATS_WIDTH, SCREEN_SIZE + PANEL_HEIGHT))
    pygame.display.set_caption("Gomoku Terminator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    human_color = BLACK if config.human == "black" else WHITE
    ai_color = _opponent(human_color)
    session = GameSession(config.rule)
    worker = AIWorker()
    game_id = uuid4().hex
    log_path = Path(config.log_file) if config.log_file else Path(config.log_dir) / f"{game_id}.json"
    log_writer = GameLogWriter(log_path)
    status = f"Human turn ({config.engine})" if human_color == BLACK else f"AI thinking ({config.engine})"
    forbidden_worker = ForbiddenOverlayWorker()
    forbidden_worker.submit(session.state, config.rule)

    undo_button = pygame.Rect(16, SCREEN_SIZE + 22, BUTTON_WIDTH, BUTTON_HEIGHT)
    restart_button = pygame.Rect(120, SCREEN_SIZE + 22, BUTTON_WIDTH, BUTTON_HEIGHT)
    running = True
    ai_started = False
    stats: list[dict] = []
    stats_scroll = 0

    while running:
        forbidden_cache = forbidden_worker.poll()
        draw_board(screen, session.state, config.rule, forbidden_cache)
        _draw_panel(screen, font, status, undo_button, restart_button, pygame)
        _draw_stats_panel(screen, font, stats, stats_scroll, pygame)

        if session.winner is None and session.current_color == ai_color and not ai_started:
            ai_started_at = time.perf_counter()
            worker.start(session.state, ai_color, AI_DEPTH, config.time_limit, config.rule, config.engine, config.threads)
            ai_started = True
            status = f"AI thinking ({config.engine})"

        if ai_started and worker.done():
            result = worker.result()
            ai_started = False
            if result is not None and result.row >= 0:
                try:
                    move = session.place(result.row, result.col, ai_color)
                    elapsed_ms = (time.perf_counter() - ai_started_at) * 1000
                    _append_log(
                        log_writer,
                        game_id,
                        session,
                        move,
                        config.rule,
                        result.depth,
                        result.nodes,
                        result.score,
                        elapsed_ms,
                    )
                    stats.append(_stats_record(move.color, move.row, move.col, result.depth, result.nodes, result.score, elapsed_ms))
                    forbidden_worker.submit(session.state, config.rule)
                    status = _status_after_move(session, human_color)
                except ValueError as exc:
                    status = f"AI illegal move: {exc}"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if undo_button.collidepoint(event.pos):
                    if ai_started:
                        ai_started = False
                    session.undo_one_human_turn()
                    if stats:
                        stats.pop()
                    forbidden_worker.submit(session.state, config.rule)
                    status = "Undo"
                    continue
                if restart_button.collidepoint(event.pos):
                    session.reset()
                    game_id = uuid4().hex
                    log_path = Path(config.log_file) if config.log_file else Path(config.log_dir) / f"{game_id}.json"
                    log_writer = GameLogWriter(log_path)
                    ai_started = False
                    stats = []
                    stats_scroll = 0
                    forbidden_worker.submit(session.state, config.rule)
                    status = f"Human turn ({config.engine})" if human_color == BLACK else f"AI thinking ({config.engine})"
                    continue

                if session.winner is not None or session.current_color != human_color or ai_started:
                    continue
                coords = get_board_coords(event.pos)
                if coords is None:
                    continue
                row, col = coords
                if config.rule == "renju" and human_color == BLACK and (row, col) in forbidden_cache:
                    status = "黑棋禁手"
                    continue
                try:
                    move = session.place(row, col, human_color)
                    _append_log(log_writer, game_id, session, move, config.rule, 0, 0, 0, 0.0)
                    forbidden_worker.submit(session.state, config.rule)
                    status = _status_after_move(session, human_color)
                except ValueError as exc:
                    status = str(exc)
            elif event.type == pygame.MOUSEWHEEL:
                stats_scroll = _scroll_stats(stats_scroll, event.y, len(stats))

        pygame.display.flip()
        clock.tick(30)

    worker.shutdown()
    forbidden_worker.shutdown()
    pygame.quit()
    return 0


def run_selfplay_mode(config) -> int:
    """启动机机模式。

    机机模式用于自博弈、benchmark 和日志生成。开启 UI 时也必须显示黑棋禁手红 X。
    """
    if not config.no_ui:
        return _run_selfplay_ui(config)

    for game_number in range(config.games):
        session = GameSession(config.rule)
        game_id = uuid4().hex
        log_path = Path(config.log_dir) / f"{game_id}.json"
        writer = GameLogWriter(log_path)
        while session.winner is None and len(session.moves) < config.max_moves:
            color = session.current_color
            started = time.perf_counter()
            result = _search_with_engine(
                session.state.copy(),
                color,
                AI_DEPTH,
                config.time_limit,
                config.rule,
                config.engine,
                config.threads,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            if result.row < 0:
                break
            move = session.place(result.row, result.col, color)
            _append_log(writer, game_id, session, move, config.rule, result.depth, result.nodes, result.score, elapsed_ms)
        print(f"selfplay game {game_number + 1}/{config.games}: {log_path}")
    return 0


def _run_selfplay_ui(config) -> int:
    """启动可观看的机机对战 UI。

    默认 selfplay 不加 `--no-ui` 时走这里。棋盘持续显示黑棋禁手红色 X，
    方便观察 AI 为什么不能走某些点。
    """

    try:
        import pygame
    except ModuleNotFoundError:
        print("Pygame is not installed. Install project dependencies before launching UI.")
        return 1

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE + STATS_WIDTH, SCREEN_SIZE + PANEL_HEIGHT))
    pygame.display.set_caption("Gomoku Terminator Selfplay")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    session = GameSession(config.rule)
    worker = AIWorker()
    game_id = uuid4().hex
    log_path = Path(config.log_file) if config.log_file else Path(config.log_dir) / f"{game_id}.json"
    log_writer = GameLogWriter(log_path)
    status = f"Selfplay ready ({config.engine})"
    forbidden_worker = ForbiddenOverlayWorker()
    forbidden_worker.submit(session.state, config.rule)
    running = True
    ai_started = False
    ai_started_at = 0.0
    restart_button = pygame.Rect(16, SCREEN_SIZE + 22, BUTTON_WIDTH, BUTTON_HEIGHT)
    pause_button = pygame.Rect(120, SCREEN_SIZE + 22, BUTTON_WIDTH, BUTTON_HEIGHT)
    paused = False
    stats: list[dict] = []
    stats_scroll = 0

    while running:
        forbidden_cache = forbidden_worker.poll()
        draw_board(screen, session.state, config.rule, forbidden_cache)
        _draw_panel(screen, font, status, restart_button, pause_button, pygame)
        _draw_stats_panel(screen, font, stats, stats_scroll, pygame)

        if not paused and session.winner is None and len(session.moves) < config.max_moves and not ai_started:
            color = session.current_color
            ai_started_at = time.perf_counter()
            worker.start(session.state, color, AI_DEPTH, config.time_limit, config.rule, config.engine, config.threads)
            ai_started = True
            status = f"{color_name(color)} thinking"

        if ai_started and worker.done():
            color = session.current_color
            result = worker.result()
            ai_started = False
            if result is not None and result.row >= 0:
                try:
                    move = session.place(result.row, result.col, color)
                    elapsed_ms = (time.perf_counter() - ai_started_at) * 1000
                    _append_log(
                        log_writer,
                        game_id,
                        session,
                        move,
                        config.rule,
                        result.depth,
                        result.nodes,
                        result.score,
                        elapsed_ms,
                    )
                    stats.append(_stats_record(move.color, move.row, move.col, result.depth, result.nodes, result.score, elapsed_ms))
                    forbidden_worker.submit(session.state, config.rule)
                    status = f"{color_name(move.color)} -> ({move.row}, {move.col})"
                except ValueError as exc:
                    status = f"AI illegal move: {exc}"
            if session.winner is not None:
                status = f"{color_name(session.winner)} wins"
            elif len(session.moves) >= config.max_moves:
                status = f"max moves reached: {log_path}"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if restart_button.collidepoint(event.pos):
                    session.reset()
                    game_id = uuid4().hex
                    log_path = Path(config.log_file) if config.log_file else Path(config.log_dir) / f"{game_id}.json"
                    log_writer = GameLogWriter(log_path)
                    ai_started = False
                    paused = False
                    stats = []
                    stats_scroll = 0
                    forbidden_worker.submit(session.state, config.rule)
                    status = "Selfplay restarted"
                elif pause_button.collidepoint(event.pos):
                    paused = not paused
                    status = "Paused" if paused else "Selfplay resumed"
            elif event.type == pygame.MOUSEWHEEL:
                stats_scroll = _scroll_stats(stats_scroll, event.y, len(stats))

        pygame.display.flip()
        clock.tick(30)

    worker.shutdown()
    forbidden_worker.shutdown()
    pygame.quit()
    print(f"selfplay ui log: {log_path}")
    return 0


def _draw_panel(screen, font, status: str, undo_button, restart_button, pygame) -> None:
    """绘制人机模式底部控制面板。"""

    panel_rect = pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, PANEL_HEIGHT)
    pygame.draw.rect(screen, (232, 218, 190), panel_rect)
    _draw_button(screen, font, undo_button, "Undo", pygame)
    _draw_button(screen, font, restart_button, "Restart", pygame)
    text = font.render(status, True, (30, 30, 30))
    screen.blit(text, (232, SCREEN_SIZE + 30))


def _draw_button(screen, font, rect, label: str, pygame) -> None:
    """绘制一个简单按钮。"""

    pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=4)
    pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=4)
    text = font.render(label, True, (20, 20, 20))
    screen.blit(text, text.get_rect(center=rect.center))


def _stats_record(color: int, row: int, col: int, depth: int, nodes: int, score: int, elapsed_ms: float) -> dict:
    """创建右侧统计面板的一条记录。"""

    nps = 0.0 if elapsed_ms <= 0 else nodes / (elapsed_ms / 1000)
    return {
        "player": color_name(color),
        "row": row,
        "col": col,
        "depth": depth,
        "nodes": nodes,
        "nps": nps,
        "score": score,
        "time_ms": elapsed_ms,
    }


def _draw_stats_panel(screen, font, stats: list[dict], scroll: int, pygame) -> None:
    """绘制右侧 AI 思考统计面板。"""

    x = SCREEN_SIZE
    height = SCREEN_SIZE + PANEL_HEIGHT
    pygame.draw.rect(screen, (31, 34, 38), pygame.Rect(x, 0, STATS_WIDTH, height))
    pygame.draw.line(screen, (82, 82, 82), (x, 0), (x, height), 1)
    screen.blit(font.render("AI Stats", True, (245, 245, 245)), (x + 16, 18))
    screen.blit(font.render("wheel: scroll", True, (170, 170, 170)), (x + 16, 44))

    end = max(0, len(stats) - scroll)
    start = max(0, end - 12)
    y = 78
    for record in stats[start:end]:
        pygame.draw.rect(screen, (42, 46, 52), pygame.Rect(x + 12, y - 6, STATS_WIDTH - 24, 82), border_radius=4)
        lines = (
            f"{record['player']} -> ({record['row']},{record['col']})",
            f"d={record['depth']} nodes={record['nodes']}",
            f"nps={record['nps']:.0f} t={record['time_ms']:.1f}ms",
            f"score={record['score']}",
        )
        for line in lines:
            screen.blit(font.render(line, True, (230, 230, 230)), (x + 20, y))
            y += 18
        y += 12


def _scroll_stats(current: int, wheel_y: int, total: int) -> int:
    """根据鼠标滚轮更新右侧统计面板滚动位置。"""

    max_scroll = max(0, total - 12)
    next_scroll = current - wheel_y
    return max(0, min(max_scroll, next_scroll))


def _append_log(
    writer: GameLogWriter,
    game_id: str,
    session: GameSession,
    move,
    rule: str,
    depth: int,
    nodes: int,
    score: int,
    time_ms: float,
) -> None:
    """追加一条对局日志。"""

    writer.append(
        MoveLog(
            game_id=game_id,
            move_number=len(session.moves),
            player=color_name(move.color),
            row=move.row,
            col=move.col,
            index=row_col_to_index(move.row, move.col),
            rule=rule,
            is_forbidden=False,
            forbidden_points=forbidden_points(session.state) if rule == "renju" else [],
            search_depth=depth,
            nodes=nodes,
            nps=0.0 if time_ms <= 0 else nodes / (time_ms / 1000),
            score=score,
            time_ms=time_ms,
            engine="human" if depth == 0 else "negamax",
            timestamp=time.time(),
        )
    )


def _status_after_move(session: GameSession, human_color: int) -> str:
    """根据局面生成状态文本。"""

    if session.winner is not None:
        return f"{color_name(session.winner)} wins"
    return "Human turn" if session.current_color == human_color else "AI thinking"
