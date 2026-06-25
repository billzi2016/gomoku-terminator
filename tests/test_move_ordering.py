from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.move_ordering import ordered_moves


def test_empty_board_orders_center_only():
    state = BitboardState()

    assert ordered_moves(state, BLACK, "renju") == [(7, 7)]


def test_non_empty_board_uses_neighborhood():
    state = BitboardState()
    state.place(7, 7, BLACK)

    moves = ordered_moves(state, BLACK, "renju")

    assert (7, 8) in moves
    assert (0, 0) not in moves
