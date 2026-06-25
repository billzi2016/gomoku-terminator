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
