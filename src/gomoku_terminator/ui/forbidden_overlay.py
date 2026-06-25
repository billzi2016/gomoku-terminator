from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.rules.renju_forbidden import forbidden_points


def current_forbidden_points(state: BitboardState, rule: str) -> list[tuple[int, int]]:
    """返回当前视图要绘制的禁手点。

    只有 Renju 规则显示黑棋禁手红色 X；自由五子棋模式不显示。
    """
    if rule != "renju":
        return []
    if _black_stone_count(state) < 4:
        return []
    return forbidden_points(state)


def _black_stone_count(state: BitboardState) -> int:
    """黑棋数量不足 4 时不可能形成 Renju 禁手，直接跳过昂贵扫描。"""

    return sum(int(word).bit_count() for word in state.black)


class ForbiddenOverlayWorker:
    """后台禁手覆盖层计算器。

    Renju 禁手扫描很贵，不能每帧在 Pygame 主线程里算。这个 worker 接收棋盘
    快照，后台计算红色 X 点位；UI 主线程只轮询结果，不会被规则计算卡死。
    """

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Future[list[tuple[int, int]]] | None = None
        self._cache: list[tuple[int, int]] = []

    @property
    def cache(self) -> list[tuple[int, int]]:
        """返回最近一次完成的禁手点缓存。"""

        return self._cache

    def submit(self, state: BitboardState, rule: str) -> None:
        """提交一次后台计算。

        传入 `state.copy()`，保证主线程继续落子或悔棋时不会影响后台快照。
        如果早期局面不可能有禁手，则同步清空缓存，不启动线程。
        """

        if rule != "renju" or _black_stone_count(state) < 4:
            self._cache = []
            self._future = None
            return
        self._future = self._executor.submit(current_forbidden_points, state.copy(), rule)

    def poll(self) -> list[tuple[int, int]]:
        """检查后台结果；未完成时返回旧缓存。"""

        if self._future is not None and self._future.done():
            self._cache = self._future.result()
            self._future = None
        return self._cache

    def shutdown(self) -> None:
        """关闭后台线程。"""

        self._executor.shutdown(wait=False, cancel_futures=True)
