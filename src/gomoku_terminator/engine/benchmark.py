from __future__ import annotations


def run_benchmark(config) -> int:
    """启动 benchmark。

    后续会输出深度、节点数、NPS、剪枝率、置换表命中率和最佳落子。
    """
    print(
        "benchmark skeleton ready: "
        f"position={config.position}, rule={config.rule}, time_limit={config.time_limit}, threads={config.threads}"
    )
    return 0
