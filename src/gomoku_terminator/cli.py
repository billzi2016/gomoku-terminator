from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    """运行时配置快照。

    argparse 解析出来的是松散 Namespace。转换成 dataclass 后，后续 UI、
    搜索、复盘、benchmark 都拿同一份结构化配置，避免各模块自己解析参数。
    """
    mode: str
    rule: str
    time_limit: float
    threads: int
    opening_book: str
    log_dir: str
    log_file: str | None
    no_ui: bool
    ai_depth: int = 4
    engine: str = "numba_bitboard"
    human: str | None = None
    games: int = 1
    max_moves: int = 225
    search_mode: str = "mild"
    position: str | None = None
    backend: str = "python"
    depth: int = 5
    scenario: str = "midgame"
    replay_file: str | None = None


def build_parser() -> argparse.ArgumentParser:
    """构建统一命令行参数解析器。

    PRD 要求所有模式都从根目录 `main.py` 进入，因此这里集中定义人机、
    机机、复盘、benchmark 的公共参数和子命令参数。
    """
    parser = argparse.ArgumentParser(
        prog="gomoku-terminator",
        description="CPU-only Gomoku/Renju engine with Pygame UI and replay tools.",
    )
    parser.add_argument("--rule", choices=("freestyle", "renju"), default="renju")
    parser.add_argument("--time-limit", type=float, default=5.0)
    parser.add_argument("--threads", type=int, default=24)
    parser.add_argument("--opening-book", default="data/opening_book.json")
    parser.add_argument("--log-dir", default="data/game_logs")
    parser.add_argument("--log-file")
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--ai-depth", type=int, default=4)
    parser.add_argument("--engine", choices=("python", "numba_bitboard"), default="numba_bitboard")
    parser.add_argument("--search-mode", "--mode", choices=("mild", "extreme"), default="mild")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    play = subparsers.add_parser("play", help="start human vs AI mode")
    play.add_argument("--human", choices=("black", "white"), default="black")

    selfplay = subparsers.add_parser("selfplay", help="start AI vs AI mode")
    selfplay.add_argument("--games", type=int, default=1)
    selfplay.add_argument("--max-moves", type=int, default=225)

    replay = subparsers.add_parser("replay", help="open a saved game log")
    replay.add_argument("replay_file")

    benchmark = subparsers.add_parser("benchmark", help="run engine benchmark")
    benchmark.add_argument("--position")
    benchmark.add_argument("--backend", choices=("python", "numba", "numba_bitboard"), default="python")
    benchmark.add_argument("--depth", type=int, default=5)
    benchmark.add_argument("--scenario", choices=("empty", "midgame"), default="midgame")

    return parser


def config_from_args(args: argparse.Namespace) -> RuntimeConfig:
    """把 argparse Namespace 转换成稳定的 RuntimeConfig。"""
    time_limit = max(0.001, float(args.time_limit))
    ai_depth = max(1, int(args.ai_depth))
    return RuntimeConfig(
        mode=args.mode,
        rule=args.rule,
        time_limit=time_limit,
        threads=args.threads,
        opening_book=args.opening_book,
        log_dir=args.log_dir,
        log_file=args.log_file,
        no_ui=args.no_ui,
        ai_depth=ai_depth,
        engine=args.engine,
        human=getattr(args, "human", None),
        games=getattr(args, "games", 1),
        max_moves=getattr(args, "max_moves", 225),
        search_mode=args.search_mode,
        position=getattr(args, "position", None),
        backend=getattr(args, "backend", "python"),
        depth=getattr(args, "depth", 5),
        scenario=getattr(args, "scenario", "midgame"),
        replay_file=getattr(args, "replay_file", None),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI 分发入口。

    这里只按 mode 分发，不在 CLI 层直接实现搜索或 Pygame 细节。
    这样以后替换 UI、搜索引擎、复盘实现时，命令行契约仍然稳定。
    """
    argv = _normalize_global_options(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)

    if config.mode == "play":
        from gomoku_terminator.ui.pygame_app import run_play_mode

        return run_play_mode(config)
    if config.mode == "selfplay":
        from gomoku_terminator.ui.pygame_app import run_selfplay_mode

        return run_selfplay_mode(config)
    if config.mode == "replay":
        from gomoku_terminator.ui.replay_view import run_replay_mode

        return run_replay_mode(config)
    if config.mode == "benchmark":
        from gomoku_terminator.engine.benchmark import run_benchmark

        return run_benchmark(config)

    parser.error(f"unknown mode: {config.mode}")
    return 2


def _normalize_global_options(argv: list[str] | None) -> list[str] | None:
    """允许全局参数写在子命令后面。

    argparse 默认要求 `--time-limit` 这类全局参数出现在子命令之前，
    但实际使用时用户更自然地写 `python main.py benchmark --time-limit 1`。
    这里把子命令后的全局参数移动到子命令前，保持命令行体验直观。
    """

    if argv is None:
        import sys

        argv = sys.argv[1:]
    else:
        argv = list(argv)

    modes = {"play", "selfplay", "replay", "benchmark"}
    value_options = {
        "--rule",
        "--time-limit",
        "--threads",
        "--opening-book",
        "--log-dir",
        "--log-file",
        "--ai-depth",
        "--engine",
        "--search-mode",
        "--mode",
    }
    flag_options = {"--no-ui"}
    mode_index = next((i for i, item in enumerate(argv) if item in modes), None)
    if mode_index is None:
        return argv

    before = argv[:mode_index]
    mode = argv[mode_index]
    after = argv[mode_index + 1 :]
    moved: list[str] = []
    kept: list[str] = []
    i = 0
    while i < len(after):
        item = after[i]
        if item in value_options and i + 1 < len(after):
            moved.extend([item, after[i + 1]])
            i += 2
        elif item in flag_options:
            moved.append(item)
            i += 1
        else:
            kept.append(item)
            i += 1
    return before + moved + [mode] + kept
