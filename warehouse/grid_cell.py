"""GridCell data model representing a single cell in the warehouse grid."""


class GridCell:
    __slots__ = ("row", "column", "walkable", "occupied")

    def __init__(self, row: int, column: int, walkable: bool = True, occupied: bool = False):
        self.row = row
        self.column = column
        self.walkable = walkable
        self.occupied = occupied

    def __repr__(self):
        return f"GridCell(row={self.row}, column={self.column}, walkable={self.walkable})"
