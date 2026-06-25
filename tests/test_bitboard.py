import pytest

from gomoku_terminator.board.bitboard import BLACK, EMPTY, WHITE, BitboardState


def test_place_and_color_lookup():
    state = BitboardState()
    state.place(7, 7, BLACK)
    state.place(7, 8, WHITE)

    assert state.color_at(7, 7) == BLACK
    assert state.color_at(7, 8) == WHITE
    assert state.color_at(7, 9) == EMPTY


def test_cannot_place_on_occupied_point():
    state = BitboardState()
    state.place(0, 0, BLACK)

    with pytest.raises(ValueError):
        state.place(0, 0, WHITE)


def test_to_matrix_snapshot():
    state = BitboardState()
    state.place(14, 14, BLACK)

    matrix = state.to_matrix()

    assert matrix[14][14] == BLACK
    assert matrix[0][0] == EMPTY
