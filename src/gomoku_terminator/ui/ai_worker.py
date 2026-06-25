from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.engine.negamax import SearchResult, search_best_move


class AIWorker:
    """Pygame 后台 AI worker。

    搜索不能跑在 Pygame 主线程里，否则 AI 思考 1 到 5 秒时窗口会卡死。
    这个类只负责把棋盘快照丢到后台线程，主线程轮询 done/result。
    """
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Future[SearchResult] | None = None

    def start(self, state: BitboardState, color: int, depth: int, time_limit: float) -> None:
        """启动一次 AI 搜索。

        传入的是 state.copy()，避免主线程继续落子或悔棋时影响后台搜索快照。
        """
        self._future = self._executor.submit(search_best_move, state.copy(), color, depth, time_limit)

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
