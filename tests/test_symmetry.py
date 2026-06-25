from gomoku_terminator.opening.symmetry import all_transforms, transform_point


def test_transform_point_rotations():
    assert transform_point(0, 0, "identity") == (0, 0)
    assert transform_point(0, 0, "rot90") == (0, 14)
    assert transform_point(0, 0, "rot180") == (14, 14)
    assert transform_point(0, 0, "rot270") == (14, 0)


def test_all_transforms_returns_8_items():
    assert len(all_transforms(7, 7)) == 8
