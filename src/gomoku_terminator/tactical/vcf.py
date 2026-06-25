from __future__ import annotations

from dataclasses import dataclass

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.engine.move_ordering import ordered_moves
from gomoku_terminator.engine.tactics import double_threat_move, immediate_win_move, immediate_win_moves


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

    if rule == "freestyle" and max_depth > 2:
        line = _search_forcing_line(state, color, max_depth, max_branch=18)
        if line:
            return TacticalResult(True, line)

    return TacticalResult(False, [])


def _opponent(color: int) -> int:
    """返回对手颜色。"""

    return WHITE if color == BLACK else BLACK


def _search_forcing_line(
    state: BitboardState,
    attacker: int,
    depth: int,
    max_branch: int,
) -> list[tuple[int, int]] | None:
    """搜索 freestyle 连续强制胜线。

    这是轻量 VCF：攻击方只考虑能制造“一步成五威胁”的落点；防守方如果只有
    一个必防点，就强制补上该点继续递归。如果攻击方制造两个及以上成五点，
    防守方无法同时挡住，直接判定找到杀线。
    """

    win = immediate_win_move(state, attacker, "freestyle")
    if win is not None:
        return [win]
    if depth <= 0:
        return None

    defender = _opponent(attacker)
    for row, col in ordered_moves(state, attacker, "freestyle")[:max_branch]:
        attack = state.copy()
        try:
            attack.place(row, col, attacker)
        except ValueError:
            continue

        wins = immediate_win_moves(attack, attacker, "freestyle")
        if len(wins) >= 2:
            return [(row, col)]
        if len(wins) != 1:
            continue

        block_row, block_col = wins[0]
        defense = attack.copy()
        try:
            defense.place(block_row, block_col, defender)
        except ValueError:
            return [(row, col)]

        child = _search_forcing_line(defense, attacker, depth - 2, max(8, max_branch - 2))
        if child:
            return [(row, col), (block_row, block_col), *child]
    return None
