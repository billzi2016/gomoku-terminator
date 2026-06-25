from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.evaluator import evaluate


def test_open_four_scores_higher_than_open_three():
    open_three = BitboardState()
    for col in (6, 7, 8):
        open_three.place(7, col, BLACK)

    open_four = BitboardState()
    for col in (6, 7, 8, 9):
        open_four.place(7, col, BLACK)

    assert evaluate(open_four, BLACK) > evaluate(open_three, BLACK)
