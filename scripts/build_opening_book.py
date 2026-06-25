from __future__ import annotations

import json
from pathlib import Path


SOURCE_NAME = "RenjuNet 26 Renju Openings"
SOURCE_URL = "https://www.renju.net/openings/"
STARTING_URL = "https://www.renju.net/starting/"
DIRECT_IMAGE_URL = "https://www.renju.net/upload/staticfiles/direct_openings.png"
INDIRECT_IMAGE_URL = "https://www.renju.net/upload/staticfiles/indirect_openings.png"


DIRECT_PATTERNS = [
    ("1D", "Kansei", "寒星", (5, 7), "sure_win_black"),
    ("2D", "Keigetsu", "渓月", (5, 8), "sure_win_black"),
    ("3D", "Sosei", "疎星", (5, 9), "balanced_slight_white"),
    ("4D", "Kagetsu", "花月", (6, 8), "sure_win_black"),
    ("5D", "Zangetsu", "残月", (6, 9), "advantage_black"),
    ("6D", "Ugetsu", "雨月", (7, 8), "sure_win_black"),
    ("7D", "Kinsei", "金星", (7, 9), "sure_win_black"),
    ("8D", "Shogetsu", "松月", (8, 7), "slight_black"),
    ("9D", "Kyugetsu", "丘月", (8, 8), "slight_black"),
    ("10D", "Shingetsu", "新月", (8, 9), "advantage_black"),
    ("11D", "Zuigetsu", "瑞星", (9, 7), "balanced_slight_black"),
    ("12D", "Sangetsu", "山月", (9, 8), "advantage_black"),
    ("13D", "Yusei", "遊星", (9, 9), "sure_win_white"),
]

INDIRECT_PATTERNS = [
    ("1I", "Chosei", "長星", (5, 9), "balanced_slight_white"),
    ("2I", "Kyogetsu", "峡月", (6, 9), "sure_win_black"),
    ("3I", "Kosei", "恒星", (7, 9), "sure_win_black"),
    ("4I", "Suigetsu", "水月", (8, 9), "sure_win_black"),
    ("5I", "Ryusei", "流星", (9, 9), "slight_white"),
    ("6I", "Ungetsu", "雲月", (7, 8), "sure_win_black"),
    ("7I", "Hogetsu", "浦月", (8, 8), "sure_win_black"),
    ("8I", "Rangetsu", "嵐月", (9, 8), "sure_win_black"),
    ("9I", "Gingetsu", "銀月", (8, 7), "advantage_black"),
    ("10I", "Myojo", "明星", (9, 7), "sure_win_black"),
    ("11I", "Shagetsu", "斜月", (8, 6), "slight_black"),
    ("12I", "Meigetsu", "名月", (9, 6), "advantage_black"),
    ("13I", "Suisei", "彗星", (9, 5), "sure_win_white"),
]


def main() -> int:
    """重建项目内置 Renju 开局库。

    这里内置的是 26 个标准开局形和少量保守推荐，不下载未授权棋谱库。
    更深的 4/5/6 手职业变化以后应通过许可证清楚的 SGF/RenLib 数据源导入。
    """

    output = Path("data/opening_book.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_book_data(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote opening book: {output}")
    return 0


def _book_data() -> dict:
    patterns = [_pattern("direct", item, (7, 7), (6, 7)) for item in DIRECT_PATTERNS]
    patterns.extend(_pattern("indirect", item, (7, 7), (6, 8)) for item in INDIRECT_PATTERNS)
    return {
        "book_version": "0.2.0",
        "board_size": 15,
        "rule": "renju",
        "coordinate": "row_col_zero_based",
        "symmetry": "entries_with_expand_symmetry_are_expanded_to_8_transforms_at_load_time",
        "quality_note": (
            "This file contains traceable canonical Renju opening patterns and conservative first moves. "
            "It is not yet a deep professional 4th/5th/6th move theory book."
        ),
        "sources": [
            {
                "name": SOURCE_NAME,
                "url": SOURCE_URL,
                "starting_url": STARTING_URL,
                "direct_image_url": DIRECT_IMAGE_URL,
                "indirect_image_url": INDIRECT_IMAGE_URL,
                "trust": "official_reference",
                "usage": "standard opening taxonomy and coordinates",
            }
        ],
        "opening_patterns": patterns,
        "entries": [
            {
                "name": "empty_board_center",
                "sequence": [],
                "move": {"row": 7, "col": 7},
                "source": SOURCE_NAME,
                "trust": "standard_first_move",
                "expand_symmetry": False,
                "note": "Renju first move is the center point.",
            },
            {
                "name": "direct_second",
                "sequence": [{"color": "black", "row": 7, "col": 7}],
                "move": {"row": 6, "col": 7},
                "source": SOURCE_NAME,
                "trust": "standard_second_move",
                "expand_symmetry": True,
                "note": "Conservative direct second move, enabling direct opening theory.",
            },
            {
                "name": "direct_sosei_third",
                "sequence": [
                    {"color": "black", "row": 7, "col": 7},
                    {"color": "white", "row": 6, "col": 7},
                ],
                "move": {"row": 5, "col": 9},
                "source": SOURCE_NAME,
                "trust": "balanced_standard_opening",
                "expand_symmetry": True,
                "note": "Direct 3, Sosei. RenjuNet describes it as mostly equal, slightly better for White.",
            },
            {
                "name": "indirect_chosei_third",
                "sequence": [
                    {"color": "black", "row": 7, "col": 7},
                    {"color": "white", "row": 6, "col": 8},
                ],
                "move": {"row": 5, "col": 9},
                "source": SOURCE_NAME,
                "trust": "balanced_standard_opening",
                "expand_symmetry": True,
                "note": "Indirect 1, Chosei. RenjuNet describes it as mostly equal, slightly better for White.",
            },
        ],
    }


def _pattern(kind: str, item: tuple[str, str, str, tuple[int, int], str], black1: tuple[int, int], white2: tuple[int, int]) -> dict:
    code, english_name, japanese_name, black3, evaluation = item
    return {
        "code": code,
        "kind": kind,
        "english_name": english_name,
        "japanese_name": japanese_name,
        "evaluation": evaluation,
        "moves": [
            {"color": "black", "row": black1[0], "col": black1[1]},
            {"color": "white", "row": white2[0], "col": white2[1]},
            {"color": "black", "row": black3[0], "col": black3[1]},
        ],
        "source": SOURCE_NAME,
    }


if __name__ == "__main__":
    raise SystemExit(main())
