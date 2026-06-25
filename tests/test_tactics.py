from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.negamax import search_best_move
from gomoku_terminator.engine.tactics import immediate_block_move, immediate_win_move


def test_immediate_win_move_finds_five():
    state = BitboardState()
    for col in (3, 4, 5, 6):
        state.place(7, col, BLACK)

    assert immediate_win_move(state, BLACK, "renju") in {(7, 2), (7, 7)}


def test_immediate_block_move_blocks_opponent_five():
    state = BitboardState()
    for col in (3, 4, 5, 6):
        state.place(7, col, WHITE)

    assert immediate_block_move(state, BLACK, "renju") in {(7, 2), (7, 7)}


def test_search_uses_immediate_win_before_deep_search():
    state = BitboardState()
    for col in (3, 4, 5, 6):
        state.place(7, col, BLACK)

    result = search_best_move(state, BLACK, depth=2, time_limit=0.01, rule="renju")

    assert (result.row, result.col) in {(7, 2), (7, 7)}
    assert result.nodes == 1
