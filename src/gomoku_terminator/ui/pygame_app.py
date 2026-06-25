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

PANEL_HEIGHT = 112
STATS_WIDTH = 560
BUTTON_HEIGHT = 42
BUTTON_WIDTH = 116
STATS_ROW_HEIGHT = 34
STATS_DETAIL_HEIGHT = 172


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
    font = pygame.font.SysFont(None, 30)

    human_color = BLACK if config.human == "black" else WHITE
    ai_color = _opponent(human_color)
    session = GameSession(config.rule)
    worker = AIWorker()
    game_id = uuid4().hex
    game_dir, log_path = _game_output_paths(config, game_id)
    log_writer = GameLogWriter(log_path)
    status = f"Human turn ({config.engine})" if human_color == BLACK else f"AI thinking ({config.engine})"
    forbidden_worker = ForbiddenOverlayWorker()
    forbidden_worker.submit(session.state, config.rule)

    undo_button = pygame.Rect(22, SCREEN_SIZE + 30, BUTTON_WIDTH, BUTTON_HEIGHT)
    restart_button = pygame.Rect(150, SCREEN_SIZE + 30, BUTTON_WIDTH, BUTTON_HEIGHT)
    running = True
    ai_started = False
    stats: list[dict] = []
    stats_scroll = 0
    saved_frame_moves = 0

    while running:
        forbidden_cache = forbidden_worker.poll()
        draw_board(screen, session.state, config.rule, forbidden_cache, _last_move_point(session))
        _draw_panel(screen, font, status, undo_button, restart_button, config, stats, pygame)
        _draw_stats_panel(screen, font, stats, stats_scroll, config, pygame)
        saved_frame_moves = _save_move_frame_if_needed(screen, game_dir, len(session.moves), saved_frame_moves, pygame)

        if session.winner is None and session.current_color == ai_color and not ai_started:
            ai_started_at = time.perf_counter()
            worker.start(
                session.state,
                ai_color,
                config.ai_depth,
                config.time_limit,
                config.rule,
                config.engine,
                config.threads,
                session.moves,
                config.opening_book,
            )
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
                        _engine_log_name(config.engine, result.nodes),
                    )
                    stats.append(
                        _stats_record(
                            len(session.moves),
                            move.color,
                            move.row,
                            move.col,
                            result.depth,
                            result.nodes,
                            result.score,
                            elapsed_ms,
                            _engine_log_name(config.engine, result.nodes),
                        )
                    )
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
                    game_dir, log_path = _game_output_paths(config, game_id)
                    log_writer = GameLogWriter(log_path)
                    ai_started = False
                    stats = []
                    stats_scroll = 0
                    saved_frame_moves = 0
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
                    _append_log(log_writer, game_id, session, move, config.rule, 0, 0, 0, 0.0, "human")
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
        _, log_path = _game_output_paths(config, game_id)
        writer = GameLogWriter(log_path)
        while session.winner is None and len(session.moves) < config.max_moves:
            color = session.current_color
            started = time.perf_counter()
            result = _search_with_engine(
                session.state.copy(),
                color,
                config.ai_depth,
                config.time_limit,
                config.rule,
                config.engine,
                config.threads,
                session.moves,
                config.opening_book,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            if result.row < 0:
                break
            move = session.place(result.row, result.col, color)
            _append_log(
                writer,
                game_id,
                session,
                move,
                config.rule,
                result.depth,
                result.nodes,
                result.score,
                elapsed_ms,
                _engine_log_name(config.engine, result.nodes),
            )
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
    font = pygame.font.SysFont(None, 30)

    session = GameSession(config.rule)
    worker = AIWorker()
    game_id = uuid4().hex
    game_dir, log_path = _game_output_paths(config, game_id)
    log_writer = GameLogWriter(log_path)
    status = f"Selfplay ready ({config.engine})"
    forbidden_worker = ForbiddenOverlayWorker()
    forbidden_worker.submit(session.state, config.rule)
    running = True
    ai_started = False
    ai_started_at = 0.0
    restart_button = pygame.Rect(22, SCREEN_SIZE + 30, BUTTON_WIDTH, BUTTON_HEIGHT)
    pause_button = pygame.Rect(150, SCREEN_SIZE + 30, BUTTON_WIDTH, BUTTON_HEIGHT)
    paused = False
    stats: list[dict] = []
    stats_scroll = 0
    saved_frame_moves = 0

    while running:
        forbidden_cache = forbidden_worker.poll()
        draw_board(screen, session.state, config.rule, forbidden_cache, _last_move_point(session))
        _draw_panel(screen, font, status, restart_button, pause_button, config, stats, pygame)
        _draw_stats_panel(screen, font, stats, stats_scroll, config, pygame)
        saved_frame_moves = _save_move_frame_if_needed(screen, game_dir, len(session.moves), saved_frame_moves, pygame)

        if not paused and session.winner is None and len(session.moves) < config.max_moves and not ai_started:
            color = session.current_color
            ai_started_at = time.perf_counter()
            worker.start(
                session.state,
                color,
                config.ai_depth,
                config.time_limit,
                config.rule,
                config.engine,
                config.threads,
                session.moves,
                config.opening_book,
            )
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
                        _engine_log_name(config.engine, result.nodes),
                    )
                    stats.append(
                        _stats_record(
                            len(session.moves),
                            move.color,
                            move.row,
                            move.col,
                            result.depth,
                            result.nodes,
                            result.score,
                            elapsed_ms,
                            _engine_log_name(config.engine, result.nodes),
                        )
                    )
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
                    game_dir, log_path = _game_output_paths(config, game_id)
                    log_writer = GameLogWriter(log_path)
                    ai_started = False
                    paused = False
                    stats = []
                    stats_scroll = 0
                    saved_frame_moves = 0
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


def _draw_panel(screen, font, status: str, undo_button, restart_button, config, stats: list[dict], pygame) -> None:
    """绘制人机模式底部控制面板。"""

    panel_rect = pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, PANEL_HEIGHT)
    pygame.draw.rect(screen, (232, 218, 190), panel_rect)
    _draw_button(screen, font, undo_button, "Undo", pygame)
    _draw_button(screen, font, restart_button, "Restart", pygame)
    text = font.render(status, True, (30, 30, 30))
    screen.blit(text, (292, SCREEN_SIZE + 42))
    _draw_runtime_line(screen, font, config, stats, pygame)


def _draw_button(screen, font, rect, label: str, pygame) -> None:
    """绘制一个简单按钮。"""

    pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=4)
    pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=4)
    text = font.render(label, True, (20, 20, 20))
    screen.blit(text, text.get_rect(center=rect.center))


def _last_move_point(session: GameSession) -> tuple[int, int] | None:
    """返回最近一手坐标，用于棋盘绿色空心圈标记。"""

    if not session.moves:
        return None
    move = session.moves[-1]
    return move.row, move.col


def _draw_runtime_line(screen, font, config, stats: list[dict], pygame) -> None:
    """在棋盘下方固定显示本局运行参数。"""

    latest_nps = _compact_number(stats[-1]["nps"]) if stats else "0"
    line = (
        f"engine {config.engine}   rule {config.rule}   "
        f"depth {config.ai_depth}   time {config.time_limit:g}s   "
        f"threads {config.threads}   speed {latest_nps} nodes/s"
    )
    text = font.render(line, True, (65, 65, 65))
    screen.blit(text, (292, SCREEN_SIZE + 76))


def _game_output_paths(config, game_id: str) -> tuple[Path, Path]:
    """返回本局输出目录和 JSON 日志路径。

    默认结构是 `data/game_logs/<game_id>/game.json`，UI 截图也保存在同一目录。
    如果用户传入 `--log-file something.json`，则使用 `something/` 作为目录名。
    """

    if config.log_file:
        requested = Path(config.log_file)
        game_dir = requested.with_suffix("") if requested.suffix else requested
    else:
        game_dir = Path(config.log_dir) / game_id
    return game_dir, game_dir / "game.json"


def _save_move_frame_if_needed(screen, game_dir: Path, move_count: int, saved_count: int, pygame) -> int:
    """每手棋保存一张整窗截图。

    文件名固定为 `001.jpg`、`002.jpg`，便于按时间顺序复盘局势。
    """

    if move_count <= 0 or move_count == saved_count:
        return saved_count
    game_dir.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, str(game_dir / f"{move_count:03d}.jpg"))
    return move_count


def _stats_record(
    move_number: int,
    color: int,
    row: int,
    col: int,
    depth: int,
    nodes: int,
    score: int,
    elapsed_ms: float,
    engine: str,
) -> dict:
    """创建右侧统计面板的一条记录。"""

    nps = 0.0 if elapsed_ms <= 0 else nodes / (elapsed_ms / 1000)
    return {
        "move_number": move_number,
        "player": color_name(color),
        "row": row,
        "col": col,
        "depth": depth,
        "nodes": nodes,
        "nps": nps,
        "score": score,
        "time_ms": elapsed_ms,
        "engine": engine,
        "source": "book" if engine.startswith("opening_book:") else "search",
    }


def _draw_stats_panel(screen, font, stats: list[dict], scroll: int, config, pygame) -> None:
    """绘制右侧 AI 思考统计面板。"""

    x = SCREEN_SIZE
    height = SCREEN_SIZE + PANEL_HEIGHT
    pygame.draw.rect(screen, (31, 34, 38), pygame.Rect(x, 0, STATS_WIDTH, height))
    pygame.draw.line(screen, (82, 82, 82), (x, 0), (x, height), 1)
    screen.blit(font.render("AI Stats", True, (245, 245, 245)), (x + 18, 16))
    summary = f"{len(stats)} AI moves  |  wheel scroll"
    screen.blit(font.render(summary, True, (166, 170, 176)), (x + 18, 48))
    pygame.draw.line(screen, (65, 70, 78), (x + 16, 78), (x + STATS_WIDTH - 16, 78), 1)

    _draw_stats_header(screen, font, x + 14, 88, pygame)
    visible_count = _visible_stats_count()
    end = max(0, len(stats) - scroll)
    start = max(0, end - visible_count)
    y = 114
    for record in stats[start:end]:
        _draw_stats_row(screen, font, record, x + 14, y, STATS_WIDTH - 28, STATS_ROW_HEIGHT - 2, pygame)
        y += STATS_ROW_HEIGHT

    detail_y = height - STATS_DETAIL_HEIGHT - 12
    pygame.draw.line(screen, (65, 70, 78), (x + 16, detail_y - 10), (x + STATS_WIDTH - 16, detail_y - 10), 1)
    if stats:
        selected = stats[max(0, min(len(stats) - 1, len(stats) - 1 - scroll))]
        _draw_stats_detail(screen, font, selected, x + 14, detail_y, STATS_WIDTH - 28, STATS_DETAIL_HEIGHT, pygame)


def _draw_stats_header(screen, font, x: int, y: int, pygame) -> None:
    """绘制统计表头。"""

    labels = (
        ("#", 0),
        ("side", 42),
        ("src", 96),
        ("pos", 154),
        ("d", 212),
        ("nodes", 252),
        ("nps", 338),
        ("time", 420),
        ("score", 480),
    )
    for label, offset in labels:
        screen.blit(font.render(label, True, (132, 138, 146)), (x + offset, y))


def _draw_stats_row(screen, font, record: dict, x: int, y: int, width: int, height: int, pygame) -> None:
    """绘制一行紧凑统计记录。"""

    source = record.get("source", "search")
    score = int(record["score"])
    accent = _score_color(score, source)
    row_color = (38, 42, 48) if record["move_number"] % 4 else (44, 48, 55)
    pygame.draw.rect(screen, row_color, pygame.Rect(x, y, width, height), border_radius=3)
    pygame.draw.rect(screen, accent, pygame.Rect(x, y, 3, height), border_radius=2)

    values = (
        (f"#{record['move_number']}", 8, (236, 238, 241)),
        (_short_player(record["player"]), 46, (236, 238, 241)),
        ("book" if source == "book" else "ai", 98, accent),
        (f"{record['row']},{record['col']}", 154, (236, 238, 241)),
        (str(record["depth"]), 216, (236, 238, 241)),
        (_compact_number(record["nodes"]), 252, (236, 238, 241)),
        (_compact_number(record["nps"]), 338, (236, 238, 241)),
        (_format_ms(record["time_ms"]), 420, (236, 238, 241)),
        (_compact_score(score), 480, _score_text_color(score)),
    )
    for value, offset, color in values:
        screen.blit(font.render(value, True, color), (x + offset, y + 5))


def _draw_stats_detail(screen, font, record: dict, x: int, y: int, width: int, height: int, pygame) -> None:
    """绘制当前选中统计记录的详情。"""

    source = record.get("source", "search")
    score = int(record["score"])
    accent = _score_color(score, source)
    card_color = (43, 47, 54) if source == "search" else (39, 52, 48)
    pygame.draw.rect(screen, card_color, pygame.Rect(x, y, width, height), border_radius=4)
    pygame.draw.rect(screen, accent, pygame.Rect(x, y, 4, height), border_radius=2)

    header = f"#{record['move_number']} {record['player']}  ({record['row']}, {record['col']})"
    screen.blit(font.render(header, True, (244, 246, 248)), (x + 12, y + 8))

    tag_rect = pygame.Rect(x + width - 72, y + 8, 58, 20)
    pygame.draw.rect(screen, accent, tag_rect, border_radius=3)
    tag_text = "BOOK" if source == "book" else "AI"
    tag_surface = font.render(tag_text, True, (20, 24, 28))
    screen.blit(tag_surface, tag_surface.get_rect(center=tag_rect.center))

    left = x + 12
    right = x + width // 2 + 6
    row1 = y + 34
    row2 = y + 56
    _draw_metric(screen, font, "depth", str(record["depth"]), left, row1)
    _draw_metric(screen, font, "nodes", _compact_number(record["nodes"]), right, row1)
    _draw_metric(screen, font, "nps", _compact_number(record["nps"]), left, row2)
    _draw_metric(screen, font, "time", _format_ms(record["time_ms"]), right, row2)

    score_text = f"score {_compact_score(score)}"
    score_color = _score_text_color(score)
    screen.blit(font.render(score_text, True, score_color), (left, y + 76))
    speed_text = f"speed {_compact_number(record['nps'])} nodes/s"
    screen.blit(font.render(speed_text, True, (190, 220, 255)), (left, y + 102))


def _draw_metric(screen, font, label: str, value: str, x: int, y: int) -> None:
    """绘制一个短指标，避免多行文本挤成一团。"""

    screen.blit(font.render(label, True, (150, 156, 164)), (x, y))
    screen.blit(font.render(value, True, (232, 235, 238)), (x + 58, y))


def _scroll_stats(current: int, wheel_y: int, total: int) -> int:
    """根据鼠标滚轮更新右侧统计面板滚动位置。"""

    max_scroll = max(0, total - _visible_stats_count())
    next_scroll = current - wheel_y
    return max(0, min(max_scroll, next_scroll))


def _visible_stats_count() -> int:
    """返回右侧统计面板当前能完整显示的表格行数。"""

    table_height = SCREEN_SIZE + PANEL_HEIGHT - STATS_DETAIL_HEIGHT - 150
    return max(1, table_height // STATS_ROW_HEIGHT)


def _short_player(player: str) -> str:
    """把颜色压缩成表格里更好扫读的短文本。"""

    return "B" if player == "black" else "W"


def _compact_number(value: float | int) -> str:
    """把节点数和 NPS 压成适合侧栏显示的短文本。"""

    number = float(value)
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.1f}k"
    return str(int(number))


def _compact_score(score: int) -> str:
    """压缩评分显示，保留必胜/必败信号。"""

    if abs(score) >= 1_000_000:
        return "WIN" if score > 0 else "LOSS"
    return str(score)


def _format_ms(value: float) -> str:
    """格式化耗时，低于 1 秒显示毫秒，高于 1 秒显示秒。"""

    if value >= 1000:
        return f"{value / 1000:.2f}s"
    return f"{value:.1f}ms"


def _score_color(score: int, source: str) -> tuple[int, int, int]:
    """返回卡片左侧强调色。"""

    if source == "book":
        return (91, 214, 154)
    if score <= -1_000_000:
        return (255, 102, 102)
    if score < 0:
        return (235, 184, 92)
    return (110, 168, 255)


def _score_text_color(score: int) -> tuple[int, int, int]:
    """返回评分文本颜色。"""

    if score <= -1_000_000:
        return (255, 122, 122)
    if score < 0:
        return (244, 197, 103)
    if score > 0:
        return (128, 198, 255)
    return (216, 220, 225)


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
    engine_name: str,
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
            engine=engine_name,
            timestamp=time.time(),
        )
    )


def _engine_log_name(engine: str, nodes: int) -> str:
    """生成对局日志中的引擎名。

    `nodes=0` 表示这手来自开局库，而不是搜索引擎实际展开节点。
    """

    return f"opening_book:{engine}" if nodes == 0 else engine


def _status_after_move(session: GameSession, human_color: int) -> str:
    """根据局面生成状态文本。"""

    if session.winner is not None:
        return f"{color_name(session.winner)} wins"
    return "Human turn" if session.current_color == human_color else "AI thinking"
