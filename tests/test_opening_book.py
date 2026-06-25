from gomoku_terminator.opening.book import OpeningBook


def test_opening_book_metadata_loads():
    book = OpeningBook.load("data/opening_book.json")

    assert book.metadata["board_size"] == 15
    assert book.lookup("missing") is None
