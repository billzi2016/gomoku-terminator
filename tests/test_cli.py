from gomoku_terminator.cli import build_parser, config_from_args, _normalize_global_options


def test_global_options_can_appear_after_subcommand():
    argv = _normalize_global_options(["benchmark", "--time-limit", "0.1", "--threads", "4"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.mode == "benchmark"
    assert config.time_limit == 0.1
    assert config.threads == 4


def test_time_limit_has_no_upper_cap():
    argv = _normalize_global_options(["benchmark", "--time-limit", "99"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.time_limit == 99.0


def test_time_limit_has_minimum_guard():
    argv = _normalize_global_options(["benchmark", "--time-limit", "0"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.time_limit == 0.001


def test_selfplay_max_moves_argument():
    argv = _normalize_global_options(["selfplay", "--games", "2", "--max-moves", "4"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.games == 2
    assert config.max_moves == 4


def test_benchmark_backend_argument():
    argv = _normalize_global_options(["benchmark", "--backend", "numba_bitboard", "--depth", "6", "--scenario", "midgame"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.backend == "numba_bitboard"
    assert config.depth == 6
    assert config.scenario == "midgame"


def test_play_engine_argument_is_explicit_python_for_now():
    argv = _normalize_global_options(["play", "--engine", "numba_bitboard"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.engine == "numba_bitboard"


def test_default_engine_is_numba_bitboard():
    argv = _normalize_global_options(["play"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.engine == "numba_bitboard"
    assert config.search_mode == "mild"


def test_search_mode_alias_can_appear_after_subcommand():
    argv = _normalize_global_options(["play", "--mode", "extreme"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.search_mode == "extreme"


def test_ai_depth_argument_can_appear_after_subcommand():
    argv = _normalize_global_options(["play", "--ai-depth", "6"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.ai_depth == 6


def test_ai_depth_has_no_upper_cap():
    argv = _normalize_global_options(["play", "--ai-depth", "99"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.ai_depth == 99


def test_ai_depth_has_minimum_guard():
    argv = _normalize_global_options(["play", "--ai-depth", "0"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.ai_depth == 1
