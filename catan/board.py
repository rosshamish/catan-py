import copy
from enum import Enum
import logging
import hexgrid
from catan import boardbuilder, states
from catan.pieces import PieceType, Piece


class Board(object):
    """
    class Board represents a catan board. It has tiles, ports, and pieces.

    A Board has pieces, which is a dictionary mapping (hexgrid.TYPE, coord) -> Piece.

    Use #place_piece, #move_piece, and #remove_piece to manage pieces on the board.

    Use #get_pieces to get all the pieces at a particular coordinate of the allowed types.
    """
    def __init__(self, terrain=None, numbers=None, ports=None, pieces=None, players=None):
        """
        Create a new board. Creation will be delegated to module boardbuilder.

        :param terrain: terrain option, boardbuilder.Opt
        :param numbers: numbers option, boardbuilder.Opt
        :param ports: ports option, boardbuilder.Opt
        :param pieces: pieces option, boardbuilder.Opt
        :param players: players option, boardbuilder.Opt
        """
        self.tiles = list()
        self.ports = list()
        self.state = states.BoardState(self)
        self.pieces = dict()

        self.opts = dict()
        if terrain is not None:
            self.opts['terrain'] = terrain
        if numbers is not None:
            self.opts['numbers'] = numbers
        if ports is not None:
            self.opts['ports'] = ports
        if pieces is not None:
            self.opts['pieces'] = pieces
        if players is not None:
            self.opts['players'] = players

        self.reset()
        self.observers = set()

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = object.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'observers':
                setattr(result, k, set(v))
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def restore(self, board):
        """
        Restore this Board object to match the properties and state of the given Board object
        :param board: properties to restore to the current (self) Board
        """
        self.tiles = board.tiles
        self.ports = board.ports

        self.state = board.state
        self.state.board = self

        self.pieces = board.pieces
        self.opts = board.opts
        self.observers = board.observers

        self.notify_observers()

    def notify_observers(self):
        for obs in self.observers:
            obs.notify(self)

    def lock(self):
        self.state = states.BoardStateLocked(self)
        for port in self.ports.copy():
            if port.type == PortType.none:
                self.ports.remove(port)
        self.notify_observers()

    def unlock(self):
        self.state = states.BoardStateModifiable(self)

    def reset(self, terrain=None, numbers=None, ports=None, pieces=None, players=None):
        opts = self.opts.copy()
        if terrain is not None:
            opts['terrain'] = terrain
        if numbers is not None:
            opts['numbers'] = numbers
        if ports is not None:
            opts['ports'] = ports
        if pieces is not None:
            opts['pieces'] = pieces
        if players is not None:
            opts['players'] = players
        boardbuilder.reset(self, opts=opts)

    def can_place_piece(self, piece, coord):
        if piece.type == PieceType.road:
            logging.warning('"Can place road" not yet implemented')
            return True
        elif piece.type == PieceType.settlement:
            logging.warning('"Can place settlement" not yet implemented')
            return True
        elif piece.type == PieceType.city:
            logging.warning('"Can place city" not yet implemented')
            return True
        elif piece.type == PieceType.robber:
            logging.warning('"Can place robber" not yet implemented')
            return True
        else:
            logging.debug('Can\'t place piece={} on coord={}'.format(
                piece.value, hex(coord)
            ))
            return self.pieces.get(coord) is None

    def place_piece(self, piece, coord):
        if not self.can_place_piece(piece, coord):
            logging.critical('ILLEGAL: Attempted to place piece={} on coord={}'.format(
                piece.value, hex(coord)
            ))
        logging.debug('Placed piece={} on coord={}'.format(
            piece, hex(coord)
        ))
        hex_type = self._piece_type_to_hex_type(piece.type)
        self.pieces[(hex_type, coord)] = piece

    def move_piece(self, piece, from_coord, to_coord):
        from_index = (self._piece_type_to_hex_type(piece.type), from_coord)
        if from_index not in self.pieces:
            logging.warning('Attempted to move piece={} which was NOT on the board'.format(from_index))
            return
        self.place_piece(piece, to_coord)
        self.remove_piece(piece, from_coord)

    def remove_piece(self, piece, coord):
        index = (self._piece_type_to_hex_type(piece.type), coord)
        try:
            self.pieces.pop(index)
            logging.debug('Removed piece={}'.format(index))
        except ValueError:
            logging.critical('Attempted to remove piece={} which was NOT on the board'.format(index))

    def get_pieces(self, types=tuple(), coord=None):
        if coord is None:
            logging.critical('Attempted to get_piece with coord={}'.format(coord))
            return Piece(None, None)
        indexes = set((self._piece_type_to_hex_type(t), coord) for t in types)
        pieces = [self.pieces[idx] for idx in indexes if idx in self.pieces]
        if len(pieces) == 0:
            #logging.warning('Found zero pieces at {}'.format(indexes))
            pass
        elif len(pieces) == 1:
            logging.debug('Found one piece at {}: {}'.format(indexes, pieces[0]))
        elif len(pieces) > 1:
            logging.debug('Found {} pieces at {}: {}'.format(len(pieces), indexes, coord, pieces))
        return pieces

    def get_port_at(self, tile_id, direction):
        """
        If no port is found, a new none port is made and added to self.ports.

        Returns the port.

        :param tile_id:
        :param direction:
        :return: Port
        """
        for port in self.ports:
            if port.tile_id == tile_id and port.direction == direction:
                return port
        port = Port(tile_id, direction, PortType.none)
        self.ports.append(port)
        return port

    def _piece_type_to_hex_type(self, piece_type):
        if piece_type in (PieceType.road, ):
            return hexgrid.EDGE
        elif piece_type in (PieceType.settlement, PieceType.city):
            return hexgrid.NODE
        elif piece_type in (PieceType.robber, ):
            return hexgrid.TILE
        else:
            logging.critical('piece type={} has no corresponding hex type. Returning None'.format(piece_type))
            return None

    def cycle_hex_type(self, tile_id):
        if self.state.modifiable():
            tile = self.tiles[tile_id - 1]
            next_idx = (list(Terrain).index(tile.terrain) + 1) % len(Terrain)
            next_terrain = list(Terrain)[next_idx]
            tile.terrain = next_terrain
        else:
            logging.debug('Attempted to cycle terrain on tile={} on a locked board'.format(tile_id))
        self.notify_observers()

    def cycle_hex_number(self, tile_id):
        if self.state.modifiable():
            tile = self.tiles[tile_id - 1]
            next_idx = (list(HexNumber).index(tile.number) + 1) % len(HexNumber)
            next_hex_number = list(HexNumber)[next_idx]
            tile.number = next_hex_number
        else:
            logging.debug('Attempted to cycle number on tile={} on a locked board'.format(tile_id))
        self.notify_observers()

    def cycle_port_type(self, tile_id, direction):
        if self.state.modifiable():
            port = self.get_port_at(tile_id, direction)
            port.type = PortType.next_ui(port.type)
        else:
            logging.debug('Attempted to cycle port on coord=({},{}) on a locked board'.format(tile_id, direction))
        self.notify_observers()

    def rotate_ports(self):
        """
        Rotates the ports 90 degrees. Useful when using the default port setup but the spectator is watching
        at a "rotated" angle from "true north".
        """
        for port in self.ports:
            port.tile_id = ((port.tile_id + 1) % len(hexgrid.coastal_tile_ids())) + 1
            port.direction = hexgrid.rotate_direction(hexgrid.EDGE, port.direction, ccw=True)
        self.notify_observers()

class Tile(object):
    """
    class Tile represents a hex tile on the catan board.

    It contains a tile identifier, a terrain type, and a number.
    """
    def __init__(self, tile_id, terrain, number):
        """
        :param tile_id: tile identifier, int, see module hexgrid
        :param terrain: Terrain
        :param number: HexNumber
        :return:
        """
        self.tile_id = tile_id
        self.terrain = terrain
        self.number = number

# Number of tiles on the catan board. This should probably be in module hexgrid.
NUM_TILES = 3+4+5+4+3


class Terrain(Enum):
    wood = 'wood'
    brick = 'brick'
    wheat = 'wheat'
    sheep = 'sheep'
    ore = 'ore'
    desert = 'desert'

    def __repr__(self):
        return self.value


class HexNumber(Enum):
    none = None
    two = 2
    three = 3
    four = 4
    five = 5
    six = 6
    eight = 8
    nine = 9
    ten = 10
    eleven = 11
    twelve = 12


class PortType(Enum):
    any4 = '4:1' # not used in UI, only used in trading
    any3 = '3:1'
    wood = 'wood'
    brick = 'brick'
    wheat = 'wheat'
    sheep = 'sheep'
    ore = 'ore'
    none = 'none' # only used in UI, not used in trading

    @classmethod
    def list_ui(cls):
        return list(filter(lambda pt: pt != PortType.any4, PortType))

    @classmethod
    def list_trading(cls):
        return list(filter(lambda pt: pt != PortType.none, PortType))

    @classmethod
    def next_ui(cls, ptype):
        types = list(PortType)
        next_idx = (types.index(ptype) + 1) % len(types)
        next_port_type = types[next_idx]
        if next_port_type == PortType.any4:
            next_port_type = PortType.next_ui(next_port_type)
        return next_port_type


class Port(object):
    """
    class Port represents a single port on the board.

    Allowed types are described in enum PortType.
    """
    def __init__(self, tile_id, direction, type):
        self.tile_id = tile_id
        self.direction = direction
        self.type = type

    def __repr__(self):
        return '{}({},{})'.format(self.type.value, self.tile_id, self.direction)

