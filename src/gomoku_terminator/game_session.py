from __future__ import annotations

from dataclasses import dataclass

from gomoku_terminator.board.bitboard import BLACK, WHITE, BitboardState
from gomoku_terminator.board.coordinates import row_col_to_index
from gomoku_terminator.rules.renju_forbidden import is_forbidden_move
from gomoku_terminator.rules.win_check import has_five_from


@dataclass(frozen=True)
class Move:
    """一手棋的结构化表示。

    日志、复盘、悔棋和 UI 都不要只传散乱 `(row, col)`，否则后续很难判断
    这一手是谁下的、是一维哪个 index、是否需要回滚。
    """

    row: int
    col: int
    color: int

    @property
    def index(self) -> int:
        """返回 PRD 约定的一维坐标。"""

        return row_col_to_index(self.row, self.col)


class GameSession:
    """一局棋的状态管理器。

    `BitboardState` 是棋盘真源，`moves` 是可复盘历史。任何落子、悔棋、
    复盘跳转都通过这个类重建状态，避免 UI 和搜索各自维护一份棋盘。
    """

    def __init__(self, rule: str = "renju") -> None:
        self.rule = rule
        self.state = BitboardState()
        self.moves: list[Move] = []
        self.winner: int | None = None

    @property
    def current_color(self) -> int:
        """返回当前轮到哪一方落子。"""

        return BLACK if len(self.moves) % 2 == 0 else WHITE

    def can_place(self, row: int, col: int, color: int) -> tuple[bool, str]:
        """判断某个颜色是否可以落在指定点。

        这里是规则真源之一：重复落子、Renju 黑棋禁手都在这里拦截。
        UI 的红色 X 只是可视化，不能替代这个判断。
        """

        if not self.state.is_empty_at(row, col):
            return False, "该位置已有棋子"
        if self.rule == "renju" and color == BLACK and is_forbidden_move(self.state, row, col):
            return False, "黑棋禁手"
        return True, ""

    def place(self, row: int, col: int, color: int | None = None) -> Move:
        """落子并更新胜负状态。"""

        color = self.current_color if color is None else color
        allowed, reason = self.can_place(row, col, color)
        if not allowed:
            raise ValueError(reason)

        self.state.place(row, col, color)
        move = Move(row, col, color)
        self.moves.append(move)
        if has_five_from(self.state, row, col, color):
            self.winner = color
        return move

    def undo_one_human_turn(self) -> None:
        """人机模式悔棋一步。

        PRD 中“悔棋一步”指撤销最近一轮人类落子和 AI 应手。如果 AI 还没应手，
        那就只撤销人类刚刚下的那一手。这里用“最多回滚两手”表达这个语义。
        """

        if not self.moves:
            return
        remove_count = 2 if len(self.moves) >= 2 else 1
        self.moves = self.moves[:-remove_count]
        self._rebuild_from_moves()

    def undo_last_move(self) -> Move | None:
        """撤销最近一手棋。

        UI 的 Undo 按钮可以连续点击，因此这里提供更细粒度的“单手回退”。
        每次回退后都从剩余历史重建棋盘，保证胜负状态、禁手覆盖和下一手颜色
        都与历史完全一致。
        """

        if not self.moves:
            return None
        removed = self.moves[-1]
        self.moves = self.moves[:-1]
        self._rebuild_from_moves()
        return removed

    def reset(self) -> None:
        """重新开始一局。"""

        self.state = BitboardState()
        self.moves = []
        self.winner = None

    def _rebuild_from_moves(self) -> None:
        """从历史落子重建 bitboard。

        这比逐个 remove 更稳，因为后续可能支持跳转到任意手数或复杂悔棋。
        """

        old_moves = list(self.moves)
        self.state = BitboardState()
        self.winner = None
        self.moves = []
        for move in old_moves:
            self.place(move.row, move.col, move.color)


def color_name(color: int) -> str:
    """把内部颜色常量转成日志/界面可读文本。"""

    return "black" if color == BLACK else "white"
