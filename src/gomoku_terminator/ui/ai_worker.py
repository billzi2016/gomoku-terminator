from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from gomoku_terminator.board.bitboard import BLACK, BitboardState
from gomoku_terminator.engine.negamax import SearchResult, search_best_move
from gomoku_terminator.engine.numba_bitboard_search import bitboard_backend_available, search_bitboard_arrays
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move


class AIWorker:
    """Pygame 后台 AI worker。

    搜索不能跑在 Pygame 主线程里，否则 AI 思考 1 到 5 秒时窗口会卡死。
    这个类只负责把棋盘快照丢到后台线程，主线程轮询 done/result。
    """
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Future[SearchResult] | None = None

    def start(
        self,
        state: BitboardState,
        color: int,
        depth: int,
        time_limit: float,
        rule: str = "renju",
        engine: str = "numba_bitboard",
        threads: int = 24,
    ) -> None:
        """启动一次 AI 搜索。

        传入的是 state.copy()，避免主线程继续落子或悔棋时影响后台搜索快照。
        """
        self._future = self._executor.submit(
            _search_with_engine,
            state.copy(),
            color,
            depth,
            time_limit,
            rule,
            engine,
            threads,
        )

    def done(self) -> bool:
        """后台搜索是否已经完成。"""
        return self._future is not None and self._future.done()

    def result(self) -> SearchResult | None:
        """获取搜索结果；未完成时返回 None。"""
        if not self.done() or self._future is None:
            return None
        return self._future.result()

    def shutdown(self) -> None:
        """关闭 worker，退出 UI 时调用。"""
        self._executor.shutdown(wait=False, cancel_futures=True)


def _search_with_engine(
    state: BitboardState,
    color: int,
    depth: int,
    time_limit: float,
    rule: str,
    engine: str,
    threads: int,
) -> SearchResult:
    """按 UI 引擎参数搜索。

    默认使用当前最高效的 `numba_bitboard`。Renju 黑棋需要完整禁手搜索；
    高速 bitboard 版还没完全实现禁手时，Renju 黑棋回退 Python，保证合法。
    """

    if engine == "numba_bitboard" and bitboard_backend_available():
        if not (rule == "renju" and color == BLACK):
            result = search_bitboard_arrays(state.black, state.white, color, depth, threads)
            if result.row >= 0:
                index = result.row * 15 + result.col
                if not state.occupied_at_index(index):
                    if not (rule == "renju" and color == BLACK and is_forbidden_move(state, result.row, result.col)):
                        return SearchResult(result.row, result.col, result.score, result.depth, result.nodes)
    return search_best_move(state, color, depth, time_limit, rule)
