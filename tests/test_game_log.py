from gomoku_terminator.logging.game_log import GameLogWriter, MoveLog
from gomoku_terminator.logging.replay_loader import load_replay


def test_game_log_round_trip(tmp_path):
    path = tmp_path / "game.json"
    writer = GameLogWriter(path)
    writer.append(MoveLog.create("game-1", 1, "black", 7, 7, 112, "renju"))

    records = load_replay(path)

    assert records[0]["game_id"] == "game-1"
    assert records[0]["row"] == 7
    assert records[0]["col"] == 7
    assert "\n  " in path.read_text(encoding="utf-8")
