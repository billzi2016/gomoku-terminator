import pytest

from gomoku_terminator.engine.numba_bitboard_search import (
    bitboard_backend_available,
    run_bitboard_benchmark,
    run_bitboard_smoke,
)


@pytest.mark.skipif(not bitboard_backend_available(), reason="numba is not installed")
def test_numba_bitboard_smoke():
    result = run_bitboard_smoke()

    assert result.occupied == 5
    assert result.win


@pytest.mark.skipif(not bitboard_backend_available(), reason="numba is not installed")
def test_numba_bitboard_benchmark_runs():
    result = run_bitboard_benchmark(depth=1, threads=1, scenario="midgame")

    assert 0 <= result.row < 15
    assert 0 <= result.col < 15
    assert result.nodes >= 1
    assert result.threads >= 1


@pytest.mark.skipif(not bitboard_backend_available(), reason="numba is not installed")
def test_numba_bitboard_prunes_midgame_candidates():
    result = run_bitboard_benchmark(depth=4, threads=1, scenario="midgame")

    assert 0 <= result.row < 15
    assert 0 <= result.col < 15
    assert result.nodes < 250_000
