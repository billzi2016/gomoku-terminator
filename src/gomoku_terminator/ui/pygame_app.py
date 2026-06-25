from __future__ import annotations


def run_play_mode(config) -> int:
    """启动人机模式。

    当前是可运行骨架；下一步会接入真正的棋盘窗口、鼠标落子、红色禁手 X、
    AI worker 和悔棋一步。
    """
    try:
        import pygame  # noqa: F401
    except ModuleNotFoundError:
        print("Pygame is not installed. Install project dependencies before launching UI.")
        return 1

    print(
        "play mode skeleton ready: "
        f"human={config.human}, rule={config.rule}, time_limit={config.time_limit}, threads={config.threads}"
    )
    return 0


def run_selfplay_mode(config) -> int:
    """启动机机模式。

    机机模式用于自博弈、benchmark 和日志生成。开启 UI 时也必须显示黑棋禁手红 X。
    """
    print(
        "selfplay mode skeleton ready: "
        f"games={config.games}, rule={config.rule}, time_limit={config.time_limit}, threads={config.threads}"
    )
    return 0
