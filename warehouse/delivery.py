"""DeliveryPoint data model."""


class DeliveryPoint:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def to_dict(self):
        return [self.row, self.col]

    def __repr__(self):
        return f"DeliveryPoint(({self.row},{self.col}))"
