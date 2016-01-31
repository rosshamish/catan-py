import copy
import logging

import hexgrid
import catanlog
import undoredo

import catan.states
import catan.board
import catan.pieces


class Game(object):
    """
    class Game represents a single game of catan. It has players, a board, and a log.

    A Game has observers. Observers register themselves by adding themselves to
    the Game's observers set. When the Game changes, it will notify all its observers,
    who can then poll the game state and make changes accordingly.

    e.g. self.game.observers.add(self)

    A Game has state. When changing state, remember to pass the current game to the
    state's constructor. This allows the state to modify the game as appropriate in
    the current state.

    e.g. self.set_state(states.GameStateNotInGame(self))
    """
    def __init__(self, players=None, board=None, logging='on', pregame='on'):
        """
        Create a Game with the given options.

        :param players: list(Player)
        :param board: Board
        :param logging: (on|off)
        :param pregame: (on|off)
        """
        self.observers = set()
        self.undo_manager = undoredo.UndoManager()
        self.options = {
            'pregame': pregame,
        }
        self.players = players or list()
        self.board = board or catan.board.Board()
        self.robber = catan.pieces.Piece(catan.pieces.PieceType.robber, None)
        if logging == 'on':
            self.catanlog = catanlog.CatanLog()
        else:
            self.catanlog = catanlog.NoopCatanLog()

        self.state = None # set in #set_state
        self.dev_card_state = None # set in #set_dev_card_state
        self._cur_player = None # set in #set_players
        self.last_roll = None # set in #roll
        self.last_player_to_roll = None # set in #roll
        self._cur_turn = 0 # incremented in #end_turn
        self.robber_tile = None # set in #move_robber

        self.board.observers.add(self)

        self.set_state(catan.states.GameStateNotInGame(self))
        self.set_dev_card_state(catan.states.DevCardNotPlayedState(self))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'observers':
                setattr(result, k, set(v))
            elif k == 'state':
                setattr(result, k, v)
            elif k == 'undo_manager':
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def do(self, command: undoredo.Command):
        """
        Does the command using the undo_manager's stack
        :param command: Command
        """
        self.undo_manager.do(command)
        self.notify_observers()

    def undo(self):
        """
        Rewind the game to the previous state.
        """
        self.undo_manager.undo()
        self.notify_observers()
        logging.debug('undo_manager undo stack={}'.format(self.undo_manager._undo_stack))

    def redo(self):
        """
        Redo the latest undone command.
        """
        self.undo_manager.redo()
        self.notify_observers()
        logging.debug('undo_manager redo stack={}'.format(self.undo_manager._redo_stack))

    def copy(self):
        """
        Return a deep copy of this Game object. See Game.__deepcopy__ for the copy implementation.
        :return: Game
        """
        return copy.deepcopy(self)

    def restore(self, game):
        """
        Restore this Game object to match the properties and state of the given Game object
        :param game: properties to restore to the current (self) Game
        """
        self.observers = game.observers
        # self.undo_manager = game.undo_manager
        self.options = game.options
        self.players = game.players
        self.board.restore(game.board)
        self.robber = game.robber
        self.catanlog = game.catanlog

        self.state = game.state
        self.state.game = self

        self.dev_card_state = game.dev_card_state

        self._cur_player = game._cur_player
        self.last_roll = game.last_roll
        self.last_player_to_roll = game.last_player_to_roll
        self._cur_turn = game._cur_turn
        self.robber_tile = game.robber_tile

        self.notify_observers()

    def notify(self, observable):
        self.notify_observers()

    def notify_observers(self):
        for obs in self.observers.copy():
            obs.notify(self)

    def set_state(self, game_state):
        _old_state = self.state
        _old_board_state = self.board.state
        self.state = game_state
        if game_state.is_in_game():
            self.board.lock()
        else:
            self.board.unlock()
        logging.info('Game now={}, was={}. Board now={}, was={}'.format(
            type(self.state).__name__,
            type(_old_state).__name__,
            type(self.board.state).__name__,
            type(_old_board_state).__name__
        ))
        self.notify_observers()

    def set_dev_card_state(self, dev_state):
        self.dev_card_state = dev_state
        self.notify_observers()

    @undoredo.undoable
    def start(self, players):
        """
        Start the game.

        The value of option 'pregame' determines whether the pregame will occur or not.

        - Resets the board
        - Sets the players
        - Sets the game state to the appropriate first turn of the game
        - Finds the robber on the board, sets the robber_tile appropriately
        - Logs the catanlog header

        :param players: players to start the game with
        """
        from .boardbuilder import Opt
        self.reset()
        if self.board.opts.get('players') == Opt.debug:
            players = Game.get_debug_players()
        self.set_players(players)
        if self.options.get('pregame') is None or self.options.get('pregame') == 'on':
            logging.debug('Entering pregame, game options={}'.format(self.options))
            self.set_state(catan.states.GameStatePreGamePlaceSettlement(self))
        elif self.options.get('pregame') == 'off':
            logging.debug('Skipping pregame, game options={}'.format(self.options))
            self.set_state(catan.states.GameStateBeginTurn(self))

        terrain = list()
        numbers = list()
        for tile in self.board.tiles:
            terrain.append(tile.terrain)
            numbers.append(tile.number)

        for (_, coord), piece in self.board.pieces.items():
            if piece.type == catan.pieces.PieceType.robber:
                self.robber_tile = hexgrid.tile_id_from_coord(coord)
                logging.debug('Found robber at coord={}, set robber_tile={}'.format(coord, self.robber_tile))

        self.catanlog.log_game_start(self.players, terrain, numbers, self.board.ports)
        self.notify_observers()

    def end(self):
        self.catanlog.log_player_wins(self.get_cur_player())
        self.set_state(catan.states.GameStateNotInGame(self))

    def reset(self):
        self.players = list()
        self.state = catan.states.GameStateNotInGame(self)

        self.last_roll = None
        self.last_player_to_roll = None
        self._cur_player = None
        self._cur_turn = 0

        self.notify_observers()

    def get_cur_player(self):
        if self._cur_player is None:
            return Player(1, 'nobody', 'nobody')
        else:
            return Player(self._cur_player.seat, self._cur_player.name, self._cur_player.color)

    def set_cur_player(self, player):
        self._cur_player = Player(player.seat, player.name, player.color)

    def set_players(self, players):
        self.players = list(players)
        self.set_cur_player(self.players[0])
        self.notify_observers()

    def cur_player_has_port_type(self, port_type):
        return self.player_has_port_type(self.get_cur_player(), port_type)

    def player_has_port_type(self, player, port_type):
        for port in self.board.ports:
            if port.type == port_type and self._player_has_port(player, port):
                return True
        return False

    def _player_has_port(self, player, port):
        edge_coord = hexgrid.edge_coord_in_direction(port.tile_id, port.direction)
        for node in hexgrid.nodes_touching_edge(edge_coord):
            pieces = self.board.get_pieces((catan.pieces.PieceType.settlement, catan.pieces.PieceType.city), node)
            if len(pieces) < 1:
                continue
            elif len(pieces) > 1:
                raise Exception('Probably a bug, num={} pieces found on node={}'.format(
                    len(pieces), node
                ))
            assert len(pieces) == 1  # will be asserted by previous if/elif combo
            piece = pieces[0]
            if piece.owner == player:
                return True
        return False

    @undoredo.undoable
    def roll(self, roll):
        self.catanlog.log_player_roll(self.get_cur_player(), roll)
        self.last_roll = roll
        self.last_player_to_roll = self.get_cur_player()
        if int(roll) == 7:
            self.set_state(catan.states.GameStateMoveRobber(self))
        else:
            self.set_state(catan.states.GameStateDuringTurnAfterRoll(self))

    @undoredo.undoable
    def move_robber(self, tile):
        self.state.move_robber(tile)

    @undoredo.undoable
    def steal(self, victim):
        if victim is None:
            victim = Player(1, 'nobody', 'nobody')
        self.state.steal(victim)

    def stealable_players(self):
        if self.robber_tile is None:
            return list()
        stealable = set()
        for node in hexgrid.nodes_touching_tile(self.robber_tile):
            pieces = self.board.get_pieces(types=(catan.pieces.PieceType.settlement, catan.pieces.PieceType.city), coord=node)
            if pieces:
                logging.debug('found stealable player={}, cur={}'.format(pieces[0].owner, self.get_cur_player()))
                stealable.add(pieces[0].owner)
        if self.get_cur_player() in stealable:
            stealable.remove(self.get_cur_player())
        logging.debug('stealable players={} at robber tile={}'.format(stealable, self.robber_tile))
        return stealable

    @undoredo.undoable
    def begin_placing(self, piece_type):
        if self.state.is_in_pregame():
            self.set_state(catan.states.GameStatePreGamePlacingPiece(self, piece_type))
        else:
            self.set_state(catan.states.GameStatePlacingPiece(self, piece_type))

    # @undoredo.undoable # state.place_road calls this, place_road is undoable
    def buy_road(self, edge):
        #self.assert_legal_road(edge)
        piece = catan.pieces.Piece(catan.pieces.PieceType.road, self.get_cur_player())
        self.board.place_piece(piece, edge)
        self.catanlog.log_player_buys_road(self.get_cur_player(), edge)
        if self.state.is_in_pregame():
            self.end_turn()
        else:
            self.set_state(catan.states.GameStateDuringTurnAfterRoll(self))

    # @undoredo.undoable # state.place_settlement calls this, place_settlement is undoable
    def buy_settlement(self, node):
        #self.assert_legal_settlement(node)
        piece = catan.pieces.Piece(catan.pieces.PieceType.settlement, self.get_cur_player())
        self.board.place_piece(piece, node)
        self.catanlog.log_player_buys_settlement(self.get_cur_player(), node)
        if self.state.is_in_pregame():
            self.set_state(catan.states.GameStatePreGamePlacingPiece(self, catan.pieces.PieceType.road))
        else:
            self.set_state(catan.states.GameStateDuringTurnAfterRoll(self))

    # @undoredo.undoable # state.place_city calls this, place_city is undoable
    def buy_city(self, node):
        #self.assert_legal_city(node)
        piece = catan.pieces.Piece(catan.pieces.PieceType.city, self.get_cur_player())
        self.board.place_piece(piece, node)
        self.catanlog.log_player_buys_city(self.get_cur_player(), node)
        self.set_state(catan.states.GameStateDuringTurnAfterRoll(self))

    @undoredo.undoable
    def buy_dev_card(self):
        self.catanlog.log_player_buys_dev_card(self.get_cur_player())
        self.notify_observers()

    @undoredo.undoable
    def place_road(self, edge_coord):
        self.state.place_road(edge_coord)

    @undoredo.undoable
    def place_settlement(self, node_coord):
        self.state.place_settlement(node_coord)

    @undoredo.undoable
    def place_city(self, node_coord):
        self.state.place_city(node_coord)

    @undoredo.undoable
    def trade(self, trade):
        giver = trade.giver().color
        giving = [(n, t.value) for n, t in trade.giving()]
        getting = [(n, t.value) for n, t in trade.getting()]
        if trade.getter() in catan.board.PortType:
            getter = trade.getter().value
            self.catanlog.log_player_trades_with_port(giver, giving, getter, getting)
            logging.debug('trading {} to port={} to get={}'.format(giving, getter, getting))
        else:
            getter = trade.getter().color
            self.catanlog.log_player_trades_with_other(giver, giving, getter, getting)
            logging.debug('trading {} to player={} to get={}'.format(giving, getter, getting))
        self.notify_observers()

    @undoredo.undoable
    def play_knight(self):
        self.set_dev_card_state(catan.states.DevCardPlayedState(self))
        self.set_state(catan.states.GameStateMoveRobberUsingKnight(self))

    @undoredo.undoable
    def play_monopoly(self, resource):
        self.catanlog.log_player_plays_dev_monopoly(self.get_cur_player(), resource)
        self.set_dev_card_state(catan.states.DevCardPlayedState(self))

    @undoredo.undoable
    def play_year_of_plenty(self, resource1, resource2):
        self.catanlog.log_player_plays_dev_year_of_plenty(self.get_cur_player(), resource1, resource2)
        self.set_dev_card_state(catan.states.DevCardPlayedState(self))

    @undoredo.undoable
    def play_road_builder(self, edge1, edge2):
        self.catanlog.log_player_plays_dev_road_builder(self.get_cur_player(), edge1, edge2)
        self.set_dev_card_state(catan.states.DevCardPlayedState(self))

    @undoredo.undoable
    def play_victory_point(self):
        self.catanlog.log_player_plays_dev_victory_point(self.get_cur_player())
        self.set_dev_card_state(catan.states.DevCardPlayedState(self))

    @undoredo.undoable
    def end_turn(self):
        self.catanlog.log_player_ends_turn(self.get_cur_player())
        self.set_cur_player(self.state.next_player())
        self._cur_turn += 1

        self.set_dev_card_state(catan.states.DevCardNotPlayedState(self))
        if self.state.is_in_pregame():
            self.set_state(catan.states.GameStatePreGamePlacingPiece(self, catan.pieces.PieceType.settlement))
        else:
            self.set_state(catan.states.GameStateBeginTurn(self))

    @classmethod
    def get_debug_players(cls):
        return [Player(1, 'yurick', 'green'),
                Player(2, 'josh', 'blue'),
                Player(3, 'zach', 'orange'),
                Player(4, 'ross', 'red')]


class Player(object):
    """class Player represents a single player on the game board.

    :param seat: integer, with 1 being top left, and increasing clockwise
    :param name: will be lowercased, spaces will be removed
    :param color: will be lowercased, spaces will be removed
    """
    def __init__(self, seat, name, color):
        if not (1 <= seat <= 4):
            raise Exception("Seat must be on [1,4]")
        self.seat = seat

        self.name = name.lower().replace(' ', '')
        self.color = color.lower().replace(' ', '')

    def __eq__(self, other):
        if other is None:
            return False
        if other.__class__ != Player:
            return False
        return (self.color == other.color
                and self.name == other.name
                and self.seat == other.seat)

    def __repr__(self):
        return '{} ({})'.format(self.color, self.name)

    def __hash__(self):
        return sum(bytes(str(self), encoding='utf8'))

