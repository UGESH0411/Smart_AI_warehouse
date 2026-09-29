"""4-Queens constraint satisfaction, framed in the project as placing charging
stations so that no two conflict (share a row, column or diagonal).

Solved with straightforward backtracking search.
"""


def solve_four_queens(n=4):
    """Returns (solutions, states_explored).
    Each solution is a list `columns` where columns[row] = column of the queen
    (charging station) placed in that row."""
    solutions = []
    states_explored = 0
    columns = [-1] * n

    def is_safe(row, col):
        for r in range(row):
            c = columns[r]
            if c == col or abs(c - col) == abs(r - row):
                return False
        return True

    def backtrack(row):
        nonlocal states_explored
        if row == n:
            solutions.append(list(columns))
            return
        for col in range(n):
            states_explored += 1
            if is_safe(row, col):
                columns[row] = col
                backtrack(row + 1)
                columns[row] = -1

    backtrack(0)
    return solutions, states_explored
