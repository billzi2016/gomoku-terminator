from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.negamax import search_best_move
from gomoku_terminator.engine.tactics import double_threat_move, immediate_block_move, immediate_win_move
from gomoku_terminator.tactical.vcf import search_vcf


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


def test_double_threat_move_detects_cross_fork():
    state = BitboardState()
    for col in (5, 6, 8):
        state.place(7, col, BLACK)
    for row in (5, 6, 8):
        state.place(row, 7, BLACK)

    assert double_threat_move(state, BLACK, "freestyle") == (7, 7)


def test_basic_vcf_reports_double_threat():
    state = BitboardState()
    for col in (5, 6, 8):
        state.place(7, col, BLACK)
    for row in (5, 6, 8):
        state.place(row, 7, BLACK)

    result = search_vcf(state, BLACK, "freestyle")

    assert result.found
    assert result.line == [(7, 7)]


def test_freestyle_vcf_reports_forcing_line():
    state = BitboardState()
    for col in (4, 5, 6):
        state.place(7, col, BLACK)
    for col in (4, 5, 6):
        state.place(8, col, BLACK)

    result = search_vcf(state, BLACK, "freestyle", max_depth=6)

    assert result.found
    assert result.line
