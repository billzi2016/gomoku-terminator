import pytest

from gomoku_terminator.engine.numba_search import numba_available, search_benchmark, search_empty_benchmark


@pytest.mark.skipif(not numba_available(), reason="numba is not installed")
def test_numba_empty_benchmark_runs():
    result = search_empty_benchmark(depth=1, threads=1)

    assert (result.row, result.col) == (7, 7)
    assert result.nodes >= 1
    assert result.threads >= 1


@pytest.mark.skipif(not numba_available(), reason="numba is not installed")
def test_numba_midgame_benchmark_has_more_work():
    empty = search_empty_benchmark(depth=1, threads=1)
    midgame = search_benchmark(depth=1, threads=1, scenario="midgame")

    assert midgame.nodes > empty.nodes
