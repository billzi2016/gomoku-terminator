from __future__ import annotations

import time

from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.negamax import search_best_move
from gomoku_terminator.engine.numba_bitboard_search import bitboard_backend_available, run_bitboard_benchmark
from gomoku_terminator.engine.numba_search import numba_available, search_benchmark


def run_benchmark(config) -> int:
    """启动 benchmark。

    后续会输出深度、节点数、NPS、剪枝率、置换表命中率和最佳落子。
    """
    if config.backend == "numba":
        if not numba_available():
            print("Numba is not installed")
            return 1
        # 第一次调用会触发 JIT 编译，不能代表真实搜索速度。先 warmup 一次，
        # 正式计时只覆盖热启动后的搜索。
        search_benchmark(depth=1, threads=config.threads, scenario=config.scenario)
        started = time.perf_counter()
        result = search_benchmark(depth=config.depth, threads=config.threads, scenario=config.scenario)
        elapsed = max(0.000001, time.perf_counter() - started)
        nps = result.nodes / elapsed
        print("backend=numba")
        print(f"rule={config.rule}")
        print(f"time_limit={config.time_limit:.3f}s")
        print(f"threads={result.threads}")
        print(f"scenario={config.scenario}")
        print(f"best_move=({result.row}, {result.col})")
        print(f"score={result.score}")
        print(f"depth={result.depth}")
        print(f"nodes={result.nodes}")
        print(f"elapsed_ms={elapsed * 1000:.2f}")
        print(f"nps={nps:.0f}")
        return 0

    if config.backend == "numba_bitboard":
        if not bitboard_backend_available():
            print("Numba is not installed")
            return 1
        run_bitboard_benchmark(depth=1, threads=config.threads, scenario=config.scenario)
        started = time.perf_counter()
        result = run_bitboard_benchmark(depth=config.depth, threads=config.threads, scenario=config.scenario)
        elapsed = max(0.000001, time.perf_counter() - started)
        nps = result.nodes / elapsed
        print("backend=numba_bitboard")
        print(f"rule={config.rule}")
        print(f"time_limit={config.time_limit:.3f}s")
        print(f"threads={result.threads}")
        print(f"scenario={config.scenario}")
        print(f"best_move=({result.row}, {result.col})")
        print(f"score={result.score}")
        print(f"depth={result.depth}")
        print(f"nodes={result.nodes}")
        print(f"elapsed_ms={elapsed * 1000:.2f}")
        print(f"nps={nps:.0f}")
        return 0

    state = BitboardState()
    started = time.perf_counter()
    result = search_best_move(state, BLACK, depth=max(1, min(config.depth, 3)), time_limit=config.time_limit, rule=config.rule)
    elapsed = max(0.000001, time.perf_counter() - started)
    nps = result.nodes / elapsed
    print("backend=python")
    print(f"rule={config.rule}")
    print(f"time_limit={config.time_limit:.3f}s")
    print(f"threads={config.threads}")
    print(f"scenario={config.scenario}")
    print(f"best_move=({result.row}, {result.col})")
    print(f"score={result.score}")
    print(f"depth={result.depth}")
    print(f"nodes={result.nodes}")
    print(f"elapsed_ms={elapsed * 1000:.2f}")
    print(f"nps={nps:.0f}")
    return 0
