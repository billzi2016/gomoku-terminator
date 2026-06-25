from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.negamax import search_best_move
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move


def test_search_does_not_return_black_forbidden_move_when_filtered():
    state = BitboardState()
    for col in range(5):
        state.place(7, col, BLACK)

    result = search_best_move(state, BLACK, depth=1, time_limit=0.1, rule="renju")

    assert (result.row, result.col) != (7, 5)
    assert not is_forbidden_move(state, result.row, result.col)
