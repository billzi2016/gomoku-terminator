from gomoku_terminator.board.coordinates import index_to_row_col, index_to_word_offset, row_col_to_index


def test_row_col_index_round_trip():
    for row in range(15):
        for col in range(15):
            index = row_col_to_index(row, col)
            assert index_to_row_col(index) == (row, col)


def test_word_offsets_cover_225_points():
    assert index_to_word_offset(0) == (0, 0)
    assert index_to_word_offset(63) == (0, 63)
    assert index_to_word_offset(64) == (1, 0)
    assert index_to_word_offset(224) == (3, 32)
