from __future__ import annotations

from dataclasses import dataclass

from gomoku_terminator.board.bitboard import BitboardState
from gomoku_terminator.engine.tactics import double_threat_move, immediate_win_move


@dataclass(frozen=True)
class TacticalResult:
    """战术搜索结果。

    found 表示是否找到杀棋；line 保存杀棋路径，供 AI 落子和复盘解释使用。
    """
    found: bool
    line: list[tuple[int, int]]


def search_vcf(state: BitboardState, color: int, rule: str = "renju", max_depth: int = 8) -> TacticalResult:
    """基础 VCF / 强制胜搜索。

    当前实现先覆盖两个最高价值场景：一手成五，以及一手制造两个及以上
    一步胜点的“双杀”。完整 VCF 会继续递归搜索冲四和唯一防守分支。
    """
    win = immediate_win_move(state, color, rule)
    if win is not None:
        return TacticalResult(True, [win])

    threat = double_threat_move(state, color, rule)
    if threat is not None:
        return TacticalResult(True, [threat])

    return TacticalResult(False, [])
