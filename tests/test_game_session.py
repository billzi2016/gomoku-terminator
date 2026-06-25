from gomoku_terminator.board.bitboard import BLACK, WHITE
from gomoku_terminator.game_session import GameSession


def test_session_places_and_tracks_current_color():
    session = GameSession()

    session.place(7, 7, BLACK)
    session.place(7, 8, WHITE)

    assert session.current_color == BLACK
    assert len(session.moves) == 2


def test_undo_one_human_turn_removes_two_moves():
    session = GameSession()
    session.place(7, 7, BLACK)
    session.place(7, 8, WHITE)

    session.undo_one_human_turn()

    assert len(session.moves) == 0
    assert session.state.is_empty_at(7, 7)
    assert session.state.is_empty_at(7, 8)


def test_session_blocks_black_forbidden_move():
    session = GameSession(rule="renju")
    for col in range(5):
        session.place(7, col, BLACK)

    allowed, reason = session.can_place(7, 5, BLACK)

    assert not allowed
    assert reason == "黑棋禁手"
