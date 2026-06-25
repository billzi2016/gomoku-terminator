from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.ui.forbidden_overlay import ForbiddenOverlayWorker, current_forbidden_points


def test_forbidden_overlay_skips_early_position():
    state = BitboardState()
    state.place(7, 7, BLACK)

    assert current_forbidden_points(state, "renju") == []


def test_forbidden_overlay_disabled_for_freestyle():
    state = BitboardState()
    for col in range(5):
        state.place(7, col, BLACK)

    assert current_forbidden_points(state, "freestyle") == []


def test_forbidden_overlay_worker_uses_fast_empty_cache_for_early_position():
    state = BitboardState()
    state.place(7, 7, BLACK)
    worker = ForbiddenOverlayWorker()

    try:
        worker.submit(state, "renju")
        assert worker.poll() == []
    finally:
        worker.shutdown()
