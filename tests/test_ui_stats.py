from gomoku_terminator.board.bitboard import BLACK
from gomoku_terminator.ui.pygame_app import _scroll_stats, _stats_record


def test_stats_record_computes_nps():
    record = _stats_record(BLACK, 7, 7, depth=2, nodes=1000, score=12, elapsed_ms=500)

    assert record["player"] == "black"
    assert record["nps"] == 2000


def test_scroll_stats_clamps_bounds():
    assert _scroll_stats(0, 1, 20) == 0
    assert _scroll_stats(0, -20, 20) == 8
