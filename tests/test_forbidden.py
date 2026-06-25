from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.rules.renju_forbidden import analyze_forbidden_move, forbidden_points


def test_black_overline_is_forbidden():
    state = BitboardState()
    for col in range(5):
        state.place(7, col, BLACK)

    result = analyze_forbidden_move(state, 7, 5)

    assert result.is_forbidden
    assert result.overline


def test_white_stones_block_forbidden_scan():
    state = BitboardState()
    state.place(7, 6, BLACK)
    state.place(7, 8, BLACK)
    state.place(7, 5, WHITE)
    state.place(7, 9, WHITE)

    result = analyze_forbidden_move(state, 7, 7)

    assert not result.overline


def test_forbidden_points_returns_coordinates():
    state = BitboardState()
    for col in range(5):
        state.place(7, col, BLACK)

    assert (7, 5) in forbidden_points(state)
