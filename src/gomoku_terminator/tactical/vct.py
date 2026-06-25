from __future__ import annotations

from gomoku_terminator.tactical.vcf import TacticalResult


def search_vct(*_args, **_kwargs) -> TacticalResult:
    """VCT 搜索占位。

    VCT 会搜索活三、冲四和连续威胁，分支比 VCF 大，但对高手局非常关键。
    """
    return TacticalResult(False, [])
