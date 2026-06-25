from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """项目根入口。

    用户会从仓库根目录执行 `python main.py ...`。源码实际放在 `src/` 下，
    所以这里先把 `src` 加入导入路径，再把控制权交给包内 CLI。
    这个文件只做入口转发，不放业务逻辑，避免后续越写越乱。
    """
    src = Path(__file__).resolve().parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from gomoku_terminator.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
