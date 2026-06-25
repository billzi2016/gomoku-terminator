from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.ui.ai_worker import _search_with_engine


def test_numba_bitboard_engine_returns_move_for_white():
    state = BitboardState()
    state.place(7, 7, BLACK)

    result = _search_with_engine(
        state,
        WHITE,
        depth=1,
        time_limit=0.01,
        rule="renju",
        engine="numba_bitboard",
        threads=1,
    )

    assert 0 <= result.row < 15
    assert 0 <= result.col < 15


def test_renju_black_uses_legal_fallback_path():
    state = BitboardState()

    result = _search_with_engine(
        state,
        BLACK,
        depth=1,
        time_limit=0.01,
        rule="renju",
        engine="numba_bitboard",
        threads=1,
    )

    assert (result.row, result.col) == (7, 7)


def test_opening_book_move_is_used_before_search():
    state = BitboardState()
    state.place(7, 7, BLACK)
    state.place(6, 7, WHITE)

    result = _search_with_engine(
        state,
        BLACK,
        depth=1,
        time_limit=0.01,
        rule="renju",
        engine="numba_bitboard",
        threads=1,
        moves=[
            {"color": "black", "row": 7, "col": 7},
            {"color": "white", "row": 6, "col": 7},
        ],
        opening_book="data/opening_book.json",
    )

    assert (result.row, result.col) == (5, 9)
    assert result.nodes == 0
