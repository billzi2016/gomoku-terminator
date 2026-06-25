from __future__ import annotations

from dataclasses import dataclass

from gomoku_terminator.board.bitboard import BLACK, EMPTY, BitboardState
from gomoku_terminator.board.coordinates import BOARD_SIZE
from gomoku_terminator.rules.win_check import DIRECTIONS, count_line, has_exact_five_from


@dataclass(frozen=True)
class ForbiddenResult:
    """黑棋禁手分析结果。

    UI 需要知道是否禁手来画红色 X；调试和复盘还需要知道原因，
    所以这里不只返回 bool，而是保留长连、四四、三三的拆分结果。
    """
    is_forbidden: bool
    overline: bool
    double_four: bool
    double_three: bool
    open_four_count: int
    open_three_count: int


def is_forbidden_move(state: BitboardState, row: int, col: int) -> bool:
    """判断黑棋落在指定点是否禁手。"""
    return analyze_forbidden_move(state, row, col).is_forbidden


def forbidden_points(state: BitboardState) -> list[tuple[int, int]]:
    """返回当前局面下所有黑棋禁手点。

    这个结果会被人机、机机观看、复盘三类棋盘视图统一用于红色 X 覆盖层。
    """
    points: list[tuple[int, int]] = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if state.color_at(row, col) == EMPTY and is_forbidden_move(state, row, col):
                points.append((row, col))
    return points


def analyze_forbidden_move(state: BitboardState, row: int, col: int) -> ForbiddenResult:
    """分析一个黑棋候选点是否禁手。

    当前实现是可测试的第一版规则骨架：先落一个临时黑子，再检查长连、
    四四和三三。Renju 三三/四四细节非常复杂，后续要继续用职业局面测试
    收紧“有效活三”和“有效四”的判定。
    """
    if state.color_at(row, col) != EMPTY:
        return ForbiddenResult(False, False, False, False, 0, 0)

    candidate = state.copy()
    candidate.place(row, col, BLACK)

    overline = any(count_line(candidate, row, col, BLACK, dr, dc) > 5 for dr, dc in DIRECTIONS)
    open_four_count = _count_four_lines(candidate)
    open_three_count = _count_open_three_lines(candidate, row, col)

    double_four = open_four_count >= 2
    double_three = open_three_count >= 2

    return ForbiddenResult(
        is_forbidden=overline or double_four or double_three,
        overline=overline,
        double_four=double_four,
        double_three=double_three,
        open_four_count=open_four_count,
        open_three_count=open_three_count,
    )


def _count_four_lines(state: BitboardState) -> int:
    """统计形成“四”的方向数。

    这里的“四”按“下一手能补成正好五连”的方向来近似。它先保证工程链路正确，
    后续会替换为更严格的 Renju 有效四判定。
    """
    lines = 0
    for dr, dc in DIRECTIONS:
        completions = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if state.color_at(row, col) != EMPTY:
                    continue
                probe = state.copy()
                probe.place(row, col, BLACK)
                if has_exact_five_from(probe, row, col, BLACK):
                    completions += 1
        if completions:
            lines += _direction_has_completion(state, dr, dc)
    return lines


def _direction_has_completion(state: BitboardState, dr: int, dc: int) -> int:
    """判断某一方向是否存在补成正好五连的空点。"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if state.color_at(row, col) != EMPTY:
                continue
            probe = state.copy()
            probe.place(row, col, BLACK)
            if count_line(probe, row, col, BLACK, dr, dc) == 5:
                return 1
    return 0


def _count_open_three_lines(state: BitboardState, row: int, col: int) -> int:
    """统计活三方向数。

    第一版用局部字符串模式识别明显活三，重点是让红色 X 和规则管线先跑起来。
    后续需要按 Renju 有效活三定义继续加强。
    """
    total = 0
    for dr, dc in DIRECTIONS:
        line = _line_text(state, row, col, dr, dc, radius=4)
        if any(pattern in line for pattern in (".BBB.", ".BB.B.", ".B.BB.")):
            total += 1
    return total


def _line_text(state: BitboardState, row: int, col: int, dr: int, dc: int, radius: int) -> str:
    """把某个方向上的局部棋形转成字符串。

    `B` 是黑棋，`W` 是白棋或边界，`.` 是空点。这样三三/四四的早期规则可以
    先用可读模式表达，等规则稳定后再位运算化。
    """
    chars: list[str] = []
    for step in range(-radius, radius + 1):
        r = row + step * dr
        c = col + step * dc
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            chars.append("W")
            continue
        color = state.color_at(r, c)
        if color == BLACK:
            chars.append("B")
        elif color == EMPTY:
            chars.append(".")
        else:
            chars.append("W")
    return "".join(chars)
