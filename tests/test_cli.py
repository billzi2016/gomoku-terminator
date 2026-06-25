from gomoku_terminator.cli import build_parser, config_from_args, _normalize_global_options


def test_global_options_can_appear_after_subcommand():
    argv = _normalize_global_options(["benchmark", "--time-limit", "0.1", "--threads", "4"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.mode == "benchmark"
    assert config.time_limit == 0.1
    assert config.threads == 4


def test_time_limit_is_capped_at_5_seconds():
    argv = _normalize_global_options(["benchmark", "--time-limit", "99"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.time_limit == 5.0


def test_selfplay_max_moves_argument():
    argv = _normalize_global_options(["selfplay", "--games", "2", "--max-moves", "4"])
    args = build_parser().parse_args(argv)
    config = config_from_args(args)

    assert config.games == 2
    assert config.max_moves == 4
