from gomoku_terminator.cli import RuntimeConfig
from gomoku_terminator.engine.benchmark import run_benchmark


def test_benchmark_runs(capsys):
    config = RuntimeConfig(
        mode="benchmark",
        rule="renju",
        time_limit=0.01,
        threads=1,
        opening_book="data/opening_book.json",
        log_dir="data/game_logs",
        log_file=None,
        no_ui=True,
        max_moves=225,
    )

    assert run_benchmark(config) == 0
    output = capsys.readouterr().out
    assert "best_move=" in output
    assert "nodes=" in output


def test_extreme_bitboard_benchmark_prints_pv(capsys):
    config = RuntimeConfig(
        mode="benchmark",
        rule="freestyle",
        time_limit=1,
        threads=1,
        opening_book="data/opening_book.json",
        log_dir="data/game_logs",
        log_file=None,
        no_ui=True,
        max_moves=225,
        backend="numba_bitboard",
        depth=2,
        scenario="midgame",
        search_mode="extreme",
    )

    assert run_benchmark(config) == 0
    output = capsys.readouterr().out
    assert "search_mode=extreme" in output
    assert "pv=" in output
