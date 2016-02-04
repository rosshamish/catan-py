"""
module boardbuilder is responsible for creating starting board layouts.

It can create a variety of boards by supplying various options.
- Options: [terrain, numbers, ports, pieces, players]
- Option values: [Opt.empty, Opt.random, Opt.preset, Opt.debug]

The default options are defined in #get_opts.

Use #get_opts to convert a dictionary mapping str->str to a dictionary
mapping str->Opts. #get_opts will also apply the default option values
for each option not supplied.

Use #build to build a new board with the passed options.

Use #modify to modify an existing board instead of building a new one.
This will reset the board. #reset is an alias.
"""
from enum import Enum
import logging
import pprint
import random
import hexgrid
import catan.game
import catan.states
import catan.board
import catan.pieces


class Opt(Enum):
    empty = 'empty'
    random = 'random'
    preset = 'preset'
    debug = 'debug'

    def __repr__(self):
        return 'opt:{}'.format(self.value)


def get_opts(opts):
    """
    Validate options and apply defaults for options not supplied.

    :param opts: dictionary mapping str->str.
    :return: dictionary mapping str->Opt. All possible keys are present.
    """
    defaults = {
        'terrain': Opt.empty,
        'numbers': Opt.empty,
        'ports': Opt.preset,
        'pieces': Opt.preset,
        'players': Opt.preset,
    }
    _opts = defaults.copy()
    if opts is None:
        opts = dict()
    try:
        for key, val in opts.copy().items():
            opts[key] = Opt(val)
        _opts.update(opts)
    except Exception:
        raise ValueError('Invalid options={}'.format(opts))
    logging.debug('used defaults=\n{}\n on opts=\n{}\nreturned total opts=\n{}'.format(
        pprint.pformat(defaults),
        pprint.pformat(opts),
        pprint.pformat(_opts)))
    return _opts


def build(opts=None):
    """
    Build a new board using the given options.
    :param opts: dictionary mapping str->Opt
    :return: the new board, Board
    """
    board = catan.board.Board()
    modify(board, opts)
    return board


def reset(board, opts=None):
    """
    Alias for #modify. Resets an existing board.
    """
    modify(board, opts)
    return None


def modify(board, opts=None):
    """
    Reset an existing board using the given options.
    :param board: the board to reset
    :param opts: dictionary mapping str->Opt
    :return: None
    """
    opts = get_opts(opts)
    board.tiles = _generate_tiles(opts['terrain'], opts['numbers'])
    board.ports = _generate_ports(opts['ports'])
    board.state = catan.states.BoardStateModifiable(board)
    board.pieces = _generate_pieces(board.tiles, board.ports, opts['players'], opts['pieces'])
    return None


def _generate_tiles(terrain_opts, numbers_opts):
    """
    Generate a list of tiles using the given terrain and numbers options.

    terrain options supported:
    - Opt.empty -> all tiles are desert
    - Opt.random -> tiles are randomized
    - Opt.preset ->
    - Opt.debug -> alias for Opt.random

    numbers options supported:
    - Opt.empty -> no tiles have numbers
    - Opt.random -> numbers are randomized
    - Opt.preset ->
    - Opt.debug -> alias for Opt.random

    :param terrain_opts: Opt
    :param numbers_opts: Opt
    :return: list(Tile)
    """
    terrain = None
    numbers = None

    if terrain_opts == Opt.empty:
        terrain = ([catan.board.Terrain.desert] * catan.board.NUM_TILES)
    elif terrain_opts in (Opt.random, Opt.debug):
        terrain = ([catan.board.Terrain.desert] +
                   [catan.board.Terrain.brick] * 3 +
                   [catan.board.Terrain.ore] * 3 +
                   [catan.board.Terrain.wood] * 4 +
                   [catan.board.Terrain.sheep] * 4 +
                   [catan.board.Terrain.wheat] * 4)
        random.shuffle(terrain)
    elif terrain_opts == Opt.preset:
        terrain = ([catan.board.Terrain.wood,
                    catan.board.Terrain.wheat,
                    catan.board.Terrain.ore,
                    catan.board.Terrain.wheat,
                    catan.board.Terrain.sheep,
                    catan.board.Terrain.brick,
                    catan.board.Terrain.sheep,
                    catan.board.Terrain.wheat,
                    catan.board.Terrain.wood,
                    catan.board.Terrain.ore,
                    catan.board.Terrain.brick,
                    catan.board.Terrain.desert,
                    catan.board.Terrain.wheat,
                    catan.board.Terrain.sheep,
                    catan.board.Terrain.wood,
                    catan.board.Terrain.ore,
                    catan.board.Terrain.sheep,
                    catan.board.Terrain.wood,
                    catan.board.Terrain.brick])

    if numbers_opts == Opt.empty:
        numbers = ([catan.board.HexNumber.none] * catan.board.NUM_TILES)
    elif numbers_opts in (Opt.random, Opt.debug):
        numbers = ([catan.board.HexNumber.two] +
                   [catan.board.HexNumber.three]*2 + [catan.board.HexNumber.four]*2 +
                   [catan.board.HexNumber.five]*2 + [catan.board.HexNumber.six]*2 +
                   [catan.board.HexNumber.eight]*2 + [catan.board.HexNumber.nine]*2 +
                   [catan.board.HexNumber.ten]*2 + [catan.board.HexNumber.eleven]*2 +
                   [catan.board.HexNumber.twelve])
        random.shuffle(numbers)
        numbers.insert(terrain.index(catan.board.Terrain.desert), catan.board.HexNumber.none)
    elif numbers_opts == Opt.preset:
        numbers = ([catan.board.HexNumber.five,
                    catan.board.HexNumber.two,
                    catan.board.HexNumber.six,
                    catan.board.HexNumber.three,
                    catan.board.HexNumber.eight,
                    catan.board.HexNumber.ten,
                    catan.board.HexNumber.nine,
                    catan.board.HexNumber.twelve,
                    catan.board.HexNumber.eleven,
                    catan.board.HexNumber.four,
                    catan.board.HexNumber.eight,
                    catan.board.HexNumber.ten,
                    catan.board.HexNumber.nine,
                    catan.board.HexNumber.four,
                    catan.board.HexNumber.five,
                    catan.board.HexNumber.six,
                    catan.board.HexNumber.three,
                    catan.board.HexNumber.eleven])
        desert_idx = terrain.index(catan.board.Terrain.desert)
        numbers.insert(desert_idx, catan.board.HexNumber.none)

    assert len(numbers) == catan.board.NUM_TILES
    assert len(terrain) == catan.board.NUM_TILES

    tile_data = list(zip(terrain, numbers))
    tiles = [catan.board.Tile(i, t, n) for i, (t, n) in enumerate(tile_data, 1)]

    return tiles


def _generate_ports(port_opts):
    """
    Generate a list of ports using the given options.

    port options supported:
    - Opt.empty ->
    - Opt.random ->
    - Opt.preset -> ports are in default locations
    - Opt.debug -> alias for Opt.preset

    :param port_opts: Opt
    :return: list(Port)
    """
    if port_opts in [Opt.preset, Opt.debug]:
        _preset_ports = [(1, 'NW', catan.board.PortType.any3),
                         (2, 'W', catan.board.PortType.wood),
                         (4, 'W', catan.board.PortType.brick),
                         (5, 'SW', catan.board.PortType.any3),
                         (6, 'SE', catan.board.PortType.any3),
                         (8, 'SE', catan.board.PortType.sheep),
                         (9, 'E', catan.board.PortType.any3),
                         (10, 'NE', catan.board.PortType.ore),
                         (12, 'NE', catan.board.PortType.wheat)]
        return [catan.board.Port(tile, dir, port_type)
                for tile, dir, port_type in _preset_ports]
    elif port_opts in [Opt.empty, Opt.random]:
        logging.warning('{} option not yet implemented'.format(port_opts))
        return []


def _generate_pieces(tiles, ports, players_opts, pieces_opts):
    """
    Generate a dictionary of pieces using the given options.

    pieces options supported:
    - Opt.empty -> no locations have pieces
    - Opt.random ->
    - Opt.preset -> robber is placed on the first desert found
    - Opt.debug -> a variety of pieces are placed around the board

    :param tiles: list of tiles from _generate_tiles
    :param ports: list of ports from _generate_ports
    :param players_opts: Opt
    :param pieces_opts: Opt
    :return: dictionary mapping (hexgrid.TYPE, coord:int) -> Piece
    """
    if pieces_opts == Opt.empty:
        return dict()
    elif pieces_opts == Opt.debug:
        players = catan.game.Game.get_debug_players()
        return {
            (hexgrid.NODE, 0x23): catan.pieces.Piece(catan.pieces.PieceType.settlement, players[0]),
            (hexgrid.EDGE, 0x22): catan.pieces.Piece(catan.pieces.PieceType.road, players[0]),
            (hexgrid.NODE, 0x67): catan.pieces.Piece(catan.pieces.PieceType.settlement, players[1]),
            (hexgrid.EDGE, 0x98): catan.pieces.Piece(catan.pieces.PieceType.road, players[1]),
            (hexgrid.NODE, 0x87): catan.pieces.Piece(catan.pieces.PieceType.settlement, players[2]),
            (hexgrid.EDGE, 0x89): catan.pieces.Piece(catan.pieces.PieceType.road, players[2]),
            (hexgrid.EDGE, 0xA9): catan.pieces.Piece(catan.pieces.PieceType.road, players[3]),
            (hexgrid.TILE, 0x77): catan.pieces.Piece(catan.pieces.PieceType.robber, None),
        }
    elif pieces_opts in (Opt.preset, ):
        deserts = filter(lambda tile: tile.terrain == catan.board.Terrain.desert, tiles)
        coord = hexgrid.tile_id_to_coord(list(deserts)[0].tile_id)
        return {
            (hexgrid.TILE, coord): catan.pieces.Piece(catan.pieces.PieceType.robber, None)
        }
    elif pieces_opts in (Opt.random, ):
        logging.warning('{} option not yet implemented'.format(pieces_opts))


def _check_red_placement(tiles):
    """
    Returns True if no red numbers are on adjacent tiles.
    Returns False if any red numbers are on adjacent tiles.

    Not yet implemented.
    """
    logging.warning('"Check red placement" not yet implemented')