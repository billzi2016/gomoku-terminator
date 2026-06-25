from __future__ import annotations

import time

from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.negamax import search_best_move


def run_benchmark(config) -> int:
    """启动 benchmark。

    后续会输出深度、节点数、NPS、剪枝率、置换表命中率和最佳落子。
    """
    state = BitboardState()
    started = time.perf_counter()
    result = search_best_move(state, BLACK, depth=2, time_limit=config.time_limit, rule=config.rule)
    elapsed = max(0.000001, time.perf_counter() - started)
    nps = result.nodes / elapsed
    print(f"rule={config.rule}")
    print(f"time_limit={config.time_limit:.3f}s")
    print(f"threads={config.threads}")
    print(f"best_move=({result.row}, {result.col})")
    print(f"score={result.score}")
    print(f"depth={result.depth}")
    print(f"nodes={result.nodes}")
    print(f"elapsed_ms={elapsed * 1000:.2f}")
    print(f"nps={nps:.0f}")
    return 0
