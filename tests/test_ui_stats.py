from types import SimpleNamespace

from gomoku_terminator.board.bitboard import BLACK
from gomoku_terminator.game_session import GameSession
from gomoku_terminator.ui.board_view import GRID_SIZE, MARGIN, SCREEN_SIZE
from gomoku_terminator.ui.pygame_app import (
    STATS_WIDTH,
    _compact_number,
    _compact_score,
    _format_ms,
    _game_output_paths,
    _last_move_point,
    _scroll_stats,
    _stats_record,
    _visible_stats_count,
)


def test_stats_record_computes_nps():
    record = _stats_record(3, BLACK, 7, 7, depth=2, nodes=1000, score=12, elapsed_ms=500, engine="numba_bitboard")

    assert record["move_number"] == 3
    assert record["player"] == "black"
    assert record["nps"] == 2000
    assert record["source"] == "search"


def test_stats_record_marks_opening_book_source():
    record = _stats_record(
        1,
        BLACK,
        7,
        7,
        depth=0,
        nodes=0,
        score=0,
        elapsed_ms=0,
        engine="opening_book:numba_bitboard",
    )

    assert record["source"] == "book"


def test_scroll_stats_clamps_bounds():
    assert _scroll_stats(0, 1, 20) == 0
    assert _scroll_stats(0, -20, 20) == max(0, 20 - _visible_stats_count())


def test_stats_formatters_are_compact():
    assert _compact_number(1_372) == "1.4k"
    assert _compact_number(1_234_567) == "1.2M"
    assert _compact_score(-1_000_000) == "LOSS"
    assert _format_ms(1847.8) == "1.85s"


def test_stats_panel_is_wide_enough_for_table():
    assert STATS_WIDTH >= 860


def test_board_view_is_scaled_up_for_readability():
    assert GRID_SIZE == 60
    assert MARGIN == 60
    assert SCREEN_SIZE == 960


def test_last_move_point_returns_recent_move():
    session = GameSession()
    assert _last_move_point(session) is None

    session.place(7, 7, BLACK)

    assert _last_move_point(session) == (7, 7)


def test_game_output_paths_use_per_game_folder():
    config = SimpleNamespace(log_file=None, log_dir="data/game_logs")

    game_dir, log_path = _game_output_paths(config, "abc123")

    assert str(game_dir) == "data/game_logs/abc123"
    assert str(log_path) == "data/game_logs/abc123/game.json"


def test_game_output_paths_convert_log_file_to_folder():
    config = SimpleNamespace(log_file="data/game_logs/manual.json", log_dir="data/game_logs")

    game_dir, log_path = _game_output_paths(config, "ignored")

    assert str(game_dir) == "data/game_logs/manual"
    assert str(log_path) == "data/game_logs/manual/game.json"
