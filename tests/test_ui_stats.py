from gomoku_terminator.board.bitboard import BLACK
from gomoku_terminator.ui.pygame_app import (
    _compact_number,
    _compact_score,
    _format_ms,
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
    assert _scroll_stats(0, -20, 20) == 20 - _visible_stats_count()


def test_stats_formatters_are_compact():
    assert _compact_number(1_372) == "1.4k"
    assert _compact_number(1_234_567) == "1.2M"
    assert _compact_score(-1_000_000) == "LOSS"
    assert _format_ms(1847.8) == "1.85s"
