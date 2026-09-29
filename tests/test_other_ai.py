from ai.four_queens import solve_four_queens
from ai.minimax import CompetitiveState, best_move_for


def test_four_queens():
    sols, states = solve_four_queens(4)
    assert sorted(sols) == [[1, 3, 0, 2], [2, 0, 3, 1]]
    assert states > 0


def test_minimax_moves_toward_valuable_package():
    s = CompetitiveState((0, 0), (5, 5), {(0, 1): 30}, 0, 0, "A")
    assert best_move_for(s, 2, 6, 6, set()) == (0, 1)
