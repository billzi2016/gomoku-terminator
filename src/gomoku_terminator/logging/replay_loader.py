from __future__ import annotations

import json
from pathlib import Path


def load_replay(path: str | Path) -> list[dict]:
    """读取 JSON 复盘文件。

    返回原始 dict 列表，方便复盘 UI 按进度条位置重建棋盘。
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    return list(data.get("moves", []))
