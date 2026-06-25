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
    human: str | None = None
    games: int = 1
    position: str | None = None
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

    subparsers = parser.add_subparsers(dest="mode", required=True)

    play = subparsers.add_parser("play", help="start human vs AI mode")
    play.add_argument("--human", choices=("black", "white"), default="black")

    selfplay = subparsers.add_parser("selfplay", help="start AI vs AI mode")
    selfplay.add_argument("--games", type=int, default=1)

    replay = subparsers.add_parser("replay", help="open a saved game log")
    replay.add_argument("replay_file")

    benchmark = subparsers.add_parser("benchmark", help="run engine benchmark")
    benchmark.add_argument("--position")

    return parser


def config_from_args(args: argparse.Namespace) -> RuntimeConfig:
    """把 argparse Namespace 转换成稳定的 RuntimeConfig。"""
    return RuntimeConfig(
        mode=args.mode,
        rule=args.rule,
        time_limit=args.time_limit,
        threads=args.threads,
        opening_book=args.opening_book,
        log_dir=args.log_dir,
        log_file=args.log_file,
        no_ui=args.no_ui,
        human=getattr(args, "human", None),
        games=getattr(args, "games", 1),
        position=getattr(args, "position", None),
        replay_file=getattr(args, "replay_file", None),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI 分发入口。

    这里只按 mode 分发，不在 CLI 层直接实现搜索或 Pygame 细节。
    这样以后替换 UI、搜索引擎、复盘实现时，命令行契约仍然稳定。
    """
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
