from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TacticalResult:
    """战术搜索结果。

    found 表示是否找到杀棋；line 保存杀棋路径，供 AI 落子和复盘解释使用。
    """
    found: bool
    line: list[tuple[int, int]]


def search_vcf(*_args, **_kwargs) -> TacticalResult:
    """VCF 搜索占位。

    后续这里只搜索连续冲四和强制防守分支，是五子棋杀力的核心模块之一。
    """
    return TacticalResult(False, [])
