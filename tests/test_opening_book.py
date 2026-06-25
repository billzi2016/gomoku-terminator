from gomoku_terminator.opening.book import OpeningBook, sequence_key
from gomoku_terminator.opening.symmetry import transform_point


def test_opening_book_metadata_loads():
    book = OpeningBook.load("data/opening_book.json")

    assert book.metadata["board_size"] == 15
    assert book.lookup("missing") is None


def test_opening_book_contains_26_standard_patterns():
    book = OpeningBook.load("data/opening_book.json")
    patterns = book.metadata["opening_patterns"]

    assert len(patterns) == 26
    assert {item["kind"] for item in patterns} == {"direct", "indirect"}
    assert {item["code"] for item in patterns} >= {"3D", "1I"}


def test_sequence_key_is_stable():
    moves = [
        {"color": "black", "row": 7, "col": 7},
        {"color": "white", "row": 6, "col": 7},
    ]

    assert sequence_key(moves) == "B7,7|W6,7"


def test_opening_book_hits_direct_sosei_third_move():
    book = OpeningBook.load("data/opening_book.json")
    move = book.lookup_moves(
        [
            {"color": "black", "row": 7, "col": 7},
            {"color": "white", "row": 6, "col": 7},
        ]
    )

    assert move is not None
    assert (move.row, move.col) == (5, 9)
    assert move.trust == "balanced_standard_opening"


def test_opening_book_expands_symmetry():
    book = OpeningBook.load("data/opening_book.json")
    move = book.lookup_moves(
        [
            {"color": "black", "row": 7, "col": 7},
            {"color": "white", "row": 7, "col": 8},
        ]
    )

    assert move is not None
    assert (move.row, move.col) == (9, 9)


def test_opening_book_expands_all_8_transforms():
    book = OpeningBook.load("data/opening_book.json")
    base_sequence = [
        {"color": "black", "row": 7, "col": 7},
        {"color": "white", "row": 6, "col": 7},
    ]
    base_move = (5, 9)
    expected_by_key = {}

    for transform in (
        "identity",
        "rot90",
        "rot180",
        "rot270",
        "flip_h",
        "flip_v",
        "diag_main",
        "diag_anti",
    ):
        transformed_sequence = [
            {
                "color": item["color"],
                "row": transform_point(item["row"], item["col"], transform)[0],
                "col": transform_point(item["row"], item["col"], transform)[1],
            }
            for item in base_sequence
        ]
        key = sequence_key(transformed_sequence)
        expected_by_key.setdefault(key, transform_point(base_move[0], base_move[1], transform))

    assert len(expected_by_key) == 4

    for key, expected in expected_by_key.items():
        transformed_sequence = [
            {"color": part[0], "row": int(part[1:].split(",")[0]), "col": int(part.split(",")[1])}
            for part in key.split("|")
        ]
        move = book.lookup_moves(transformed_sequence)

        assert move is not None
        assert (move.row, move.col) == expected
