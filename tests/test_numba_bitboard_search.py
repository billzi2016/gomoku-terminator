import pytest

from gomoku_terminator.engine.numba_bitboard_search import bitboard_backend_available, run_bitboard_smoke


@pytest.mark.skipif(not bitboard_backend_available(), reason="numba is not installed")
def test_numba_bitboard_smoke():
    result = run_bitboard_smoke()

    assert result.occupied == 5
    assert result.win
