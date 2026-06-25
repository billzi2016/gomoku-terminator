from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    output = Path("data/opening_book.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        print(f"opening book already exists: {output}")
        return 0

    output.write_text(
        json.dumps(
            {
                "book_version": "0.1.0",
                "board_size": 15,
                "rule": "renju",
                "coordinate": "row_col_zero_based",
                "sources": [],
                "entries": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"created opening book skeleton: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
