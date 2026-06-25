from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.rules.win_check import has_five_from, has_winner


def test_horizontal_five():
    state = BitboardState()
    for col in range(5):
        state.place(7, col, BLACK)

    assert has_five_from(state, 7, 2, BLACK)
    assert has_winner(state, BLACK)


def test_diagonal_five():
    state = BitboardState()
    for i in range(5):
        state.place(i, i, WHITE)

    assert has_five_from(state, 2, 2, WHITE)
    assert has_winner(state, WHITE)
