from enum import Enum


class PieceType(Enum):
    settlement = 'settlement'
    road = 'road'
    city = 'city'
    robber = 'robber'


class Piece(object):
    """
    class Piece represents a single game piece on the board.

    Allowed types are described in enum PieceType
    """
    def __init__(self, type, owner):
        self.type = type
        self.owner = owner

    def __repr__(self):
        return '<Piece type={}, owner={}>'.format(self.type.value, self.owner)
