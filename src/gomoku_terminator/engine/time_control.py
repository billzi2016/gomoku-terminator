from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TimeControl:
    """搜索时间控制器。

    PRD 要求 AI 单步硬上限 5 秒。搜索循环必须频繁检查 expired，
    超时就返回当前最佳结果，不能让 UI 长时间无响应。
    """
    limit_seconds: float
    started_at: float = 0.0

    def start(self) -> None:
        """记录搜索开始时间。"""
        self.started_at = time.perf_counter()

    def elapsed(self) -> float:
        """返回已经用掉的秒数。"""
        if self.started_at == 0.0:
            return 0.0
        return time.perf_counter() - self.started_at

    def expired(self) -> bool:
        """是否超过本步搜索时间上限。"""
        return self.elapsed() >= self.limit_seconds
