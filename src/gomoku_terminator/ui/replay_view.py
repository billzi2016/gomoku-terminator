from __future__ import annotations


def run_replay_mode(config) -> int:
    """启动复盘模式。

    后续会加载 JSON Lines log，提供进度条拖拽和相邻的上一步 / 下一步按钮。
    """
    print(f"replay mode skeleton ready: {config.replay_file}")
    return 0
