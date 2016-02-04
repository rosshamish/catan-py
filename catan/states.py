"""
module states provides catan state machines which semi-correctly implement the State Pattern

State Pattern: https://en.wikipedia.org/wiki/State_pattern

The Game has a state whose type is one of the GameState types defined in this module.
The Game has a dev card state whose type is one of the DevCardPlayabilityState types defined in this module.
The Board has a state whose type is one of the BoardState types defined in this module.

Each state machine is described in base state's docstring.

Actions
-------

Callers should invoke action methods on the object directly, and the object will delegate
actions to its state as necessary.

e.g.
    # class Game
    def steal(self, victim):
        if victim is None:
            victim = Player(1, 'nobody', 'nobody')
        self.state.steal(victim)
    # class GameStateSteal
    def steal(self, victim):
        self.game.catanlog.log_player_moves_robber_and_steals(
            self.game.get_cur_player(),
            self.game.robber_tile,
            victim
        )
        self.game.set_state(GameStateDuringTurnAfterRoll(self.game))
    # class GameStateStealUsingKnight
    def steal(self, victim):
        self.game.catanlog.log_player_plays_dev_knight(
            self.game.get_cur_player(),
            self.game.robber_tile,
            victim
        )
        self.game.set_state(GameStateDuringTurnAfterRoll(self.game))

State Capabilities
------------------

Callers should query state capabilities through the state.

e.g.
    if game.state.can_trade():
        tradingUI.show()
    else:
        tradingUI.hide()

Any new state capabilities must be named like can_do_xyz() and must return True or False.
When a GameState subclass doesn't implement can_do_xyz2(), the method call will be caught in
GameState.__getattr__. The method call will be ignored and None will be returned instead.

If the method does not look like can_do_xyz(), it will be logged.

"""
import logging
import hexgrid
import catan.pieces


class GameState(object):
    """
    class GameState is the base game state. All game states inherit from GameState.

    sub-states are always allowed to override provided methods.

    this state implements:
        None
    this state provides:
        None
    sub-states must implement:
        is_in_game()
    """
    def __init__(self, game):
        self.game = game

    def __getattr__(self, name):
        """Return false for methods called on GameStates which don't have those methods.
        This should be ok, since __getattr__ is only called as a last resort
        i.e. if there are no attributes in the instance that match the name

        source: http://stackoverflow.com/a/2405617/1817465
        """
        def method(*args):
            return None
        if 'can_' not in name:
            # can_do_xyz methods are ok to return None if not implemented
            logging.debug('Method {0} not found'.format(name))
        return method

    def is_in_game(self):
        """
        See GameStateInGame for details.

        :return Boolean
        """
        pass


class GameStateNotInGame(GameState):
    """
    All NOT-IN-GAME states inherit from this state.

    See GameStateInGame for details.

    this state implements:
        is_in_game()
    this state provides:
        None
    sub-classes must implement:
        None
    """
    def is_in_game(self):
        return False


class GameStateNotInGameMoveRobber(GameStateNotInGame):
    """
    Moving the robber while setting up the board.
    """
    def can_move_robber(self):
        return True

    def move_robber(self, tile_id):
        robbers = self.game.board.get_pieces((catan.pieces.PieceType.robber, ),
                                             hexgrid.tile_id_to_coord(self.game.robber_tile))
        to_coord = hexgrid.tile_id_to_coord(tile_id)
        if robbers:
            robber = robbers[0]
            from_coord = hexgrid.tile_id_to_coord(self.game.robber_tile)
            self.game.board.move_piece(robber, from_coord, to_coord)
        else:
            robber = catan.pieces.Piece(catan.pieces.PieceType.robber, None)
            self.game.board.place_piece(robber, to_coord)
        if len(robbers) != 1:
            logging.warning('{} robbers found in board.pieces'.format(len(robbers)))
        self.game.robber_tile = tile_id
        self.game.set_state(GameStateNotInGame(self.game))


class GameStateInGame(GameState):
    """
    All IN-GAME states inherit from this state.

    In game is defined as taking turns, rolling dice, placing pieces, etc.
    In game starts on 'Start Game', and ends on 'End Game'

    this state implements:
        is_in_game()
    this state provides:
        is_in_pregame()
        next_player()
        begin_turn()
        has_rolled()
        can_roll()
        can_move_robber()
        can_steal()
        can_buy_road()
        can_buy_settlement()
        can_buy_city()
        can_buy_dev_card()
        can_trade()
        can_play_knight()
        can_play_monopoly()
        can_play_road_builder()
        can_play_victory_point()
    sub-states must implement:
        can_end_turn()
    """
    def is_in_game(self):
        return True

    def is_in_pregame(self):
        """
        See GameStatePreGame for details.

        :return: Boolean
        """
        return False

    def next_player(self):
        """
        Returns the player whose turn it will be next.

        Uses regular seat-wise clockwise rotation.

        Compare to GameStatePreGame's implementation, which uses snake draft.

        :return Player
        """
        logging.warning('turn={}, players={}'.format(
            self.game._cur_turn,
            self.game.players
        ))
        return self.game.players[(self.game._cur_turn + 1) % len(self.game.players)]

    def begin_turn(self):
        """
        Begins the turn for the current player.

        All that is required is to set the game's state.

        Compare to GameStatePreGame's implementation, which uses GameStatePreGamePlaceSettlement

        :return None
        """
        self.game.set_state(GameStateBeginTurn(self.game))

    def has_rolled(self):
        """
        Whether the current player has rolled or not.

        :return Boolean
        """
        return self.game.last_player_to_roll == self.game.get_cur_player()

    def can_roll(self):
        """
        Whether the current player can roll or not.

        A player can roll only if they have not yet rolled.

        :return Boolean
        """
        return not self.has_rolled()

    def can_move_robber(self):
        """
        Whether the current player can move the robber or not.

        :return Boolean
        """
        return False

    def can_steal(self):
        """
        Whether the current player can steal or not.

        :return Boolean
        """
        return False

    def can_buy_road(self):
        """
        Whether the current player can buy a road or not.

        :return Boolean
        """
        return self.has_rolled()

    def can_buy_settlement(self):
        """
        Whether the current player can buy a settlement or not.

        :return Boolean
        """
        return self.has_rolled()

    def can_buy_city(self):
        """
        Whether the current player can buy a city or not.

        :return Boolean
        """
        return self.has_rolled()

    def can_place_road(self):
        """
        Whether the current player can place a road or not.

        :return Boolean
        """
        return False

    def can_place_settlement(self):
        """
        Whether the current player can place a settlement or not.

        :return Boolean
        """
        return False

    def can_place_city(self):
        """
        Whether the current player can place a city or not.

        :return Boolean
        """
        return False

    def can_buy_dev_card(self):
        """
        Whether the current player can buy a dev card or not.

        :return Boolean
        """
        return self.has_rolled()

    def can_trade(self):
        """
        Whether the current player can trade or not.

        :return Boolean
        """
        return self.has_rolled()

    def can_play_knight(self):
        """
        Whether the current player can play a knight dev card or not.

        :return Boolean
        """
        return self.game.dev_card_state.can_play_dev_card()

    def can_play_monopoly(self):
        """
        Whether the current player can play a monopoly dev card or not.

        :return Boolean
        """
        return self.has_rolled() and self.game.dev_card_state.can_play_dev_card()

    def can_play_year_of_plenty(self):
        """
        Whether the current player can play a year of plenty dev card or not.

        :return Boolean
        """
        return self.has_rolled() and self.game.dev_card_state.can_play_dev_card()

    def can_play_road_builder(self):
        """
        Whether the current player can play a road builder dev card or not.

        :return Boolean
        """
        return self.has_rolled() and self.game.dev_card_state.can_play_dev_card()

    def can_play_victory_point(self):
        """
        Whether the current player can play a victory point dev card or not.

        :return Boolean
        """
        return True

    def can_end_turn(self):
        """
        Whether the current player can end their turn or not.

        :return Boolean
        """
        raise NotImplemented()


class GameStatePreGame(GameStateInGame):
    """
    The pregame is defined as
    - AFTER the board has been laid out
    - BEFORE the first dice roll

    In other words, it is the placing of the initial settlements and roads, in snake draft order.

    this state implements:
        can_end_turn()

    this state provides:
        None
    sub-classes must implement:
        None
    """
    def can_end_turn(self):
        return False

    def is_in_pregame(self):
        return True

    def next_player(self):
        snake = self.game.players.copy()
        snake += list(reversed(snake))
        try:
            return snake[self.game._cur_turn + 1]
        except IndexError:
            self.game.set_state(GameStateBeginTurn(self.game))
            return self.game.state.next_player()

    def begin_turn(self):
        self.game.set_state(GameStatePreGamePlaceSettlement(self.game))

    def can_play_knight(self):
        """No dev cards in the pregame"""
        return False

    def can_play_monopoly(self):
        """No dev cards in the pregame"""
        return False

    def can_play_road_builder(self):
        """No dev cards in the pregame"""
        return False

    def can_play_victory_point(self):
        """No dev cards in the pregame"""
        return False

    def can_roll(self):
        """No rolling in the pregame"""
        return False

    def can_buy_road(self):
        raise NotImplemented()

    def can_buy_settlement(self):
        raise NotImplemented()

    def can_buy_city(self):
        """No cities in the pregame"""
        return False

    def can_buy_dev_card(self):
        """No dev cards in the pregame"""
        return False

    def can_trade(self):
        """No trading in the pregame"""
        return False


class GameStatePreGamePlaceSettlement(GameStatePreGame):
    """
    - AFTER a player's turn has started
    - BEFORE the player has placed an initial settlement
    """
    def can_buy_settlement(self):
        return True

    def can_buy_road(self):
        return False

    def can_end_turn(self):
        return False


class GameStatePreGamePlaceRoad(GameStatePreGame):
    """
    - AFTER a player has placed an initial settlement
    - BEFORE the player has placed an initial road
    """
    def can_buy_settlement(self):
        return False

    def can_buy_road(self):
        return True

    def can_end_turn(self):
        return False


class GameStatePreGamePlacingPiece(GameStatePreGame):
    """
    - AFTER a player has selected to place a piece
    - WHILE the player is choosing where to place it
    - BEFORE the player has placed it
    """
    def __init__(self, game, piece_type):
        super(GameStatePreGamePlacingPiece, self).__init__(game)
        self.piece_type = piece_type

    def can_buy_settlement(self):
        return False

    def can_buy_road(self):
        return False

    def can_end_turn(self):
        return False

    def can_place_road(self):
        return self.piece_type == catan.pieces.PieceType.road

    def can_place_settlement(self):
        return self.piece_type == catan.pieces.PieceType.settlement

    def can_place_city(self):
        return self.piece_type == catan.pieces.PieceType.city

    def place_road(self, edge):
        if not self.can_place_road():
            logging.warning('Attempted to place road in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_road(edge)

    def place_settlement(self, node):
        if not self.can_place_settlement():
            logging.warning('Attempted to place settlement in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_settlement(node)

    def place_city(self, node):
        if not self.can_place_city():
            logging.warning('Attempted to place city in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_city(node)

class GameStateBeginTurn(GameStateInGame):
    """
    The start of the turn is defined as
    - AFTER the previous player ends their turn
    - BEFORE the next player's first action
    """
    def can_end_turn(self):
        return False


class GameStateMoveRobber(GameStateInGame):
    """
    Defined as
    - AFTER the rolling of a 7
    - BEFORE the player has moved the robber
    """
    def can_end_turn(self):
        return False

    def can_move_robber(self):
        return True

    def move_robber(self, tile_id):
        robbers = self.game.board.get_pieces((catan.pieces.PieceType.robber, ),
                                             hexgrid.tile_id_to_coord(self.game.robber_tile))
        for robber in robbers:
            self.game.board.move_piece(robber,
                                       hexgrid.tile_id_to_coord(self.game.robber_tile), hexgrid.tile_id_to_coord(tile_id))
        if len(robbers) != 1:
            logging.warning('{} robbers found in board.pieces'.format(len(robbers)))
        self.game.robber_tile = tile_id
        self.game.set_state(GameStateSteal(self.game))

    def can_roll(self):
        return False

    def can_buy_road(self):
        return False

    def can_buy_settlement(self):
        return False

    def can_buy_city(self):
        return False

    def can_buy_dev_card(self):
        return False

    def can_trade(self):
        return False

    def can_play_knight(self):
        return False

    def can_play_monopoly(self):
        return False

    def can_play_road_builder(self):
        return False


class GameStateMoveRobberUsingKnight(GameStateMoveRobber):
    """
    Defined as
    - AFTER the playing of a knight
    - BEFORE the player has moved the robber
    """
    def move_robber(self, tile_id):
        robbers = self.game.board.get_pieces((catan.pieces.PieceType.robber, ),
                                             hexgrid.tile_id_to_coord(self.game.robber_tile))
        for robber in robbers:
            self.game.board.move_piece(robber,
                                       hexgrid.tile_id_to_coord(self.game.robber_tile), hexgrid.tile_id_to_coord(tile_id))
        if len(robbers) > 1:
            logging.warning('More than one robber found in board.pieces')
        self.game.robber_tile = tile_id
        self.game.set_state(GameStateStealUsingKnight(self.game))


class GameStateSteal(GameStateInGame):
    """
    Defined as
    - AFTER the player has moved the robber
    - BEFORE the player has stolen a card
    """
    def can_end_turn(self):
        return False

    def can_steal(self):
        return True

    def steal(self, victim):
        self.game.catanlog.log_player_moves_robber_and_steals(
            self.game.get_cur_player(),
            hexgrid.location(hexgrid.TILE, self.game.robber_tile),
            victim
        )
        self.game.set_state(GameStateDuringTurnAfterRoll(self.game))

    def can_roll(self):
        return False

    def can_buy_road(self):
        return False

    def can_buy_settlement(self):
        return False

    def can_buy_city(self):
        return False

    def can_buy_dev_card(self):
        return False

    def can_trade(self):
        return False

    def can_play_knight(self):
        return False

    def can_play_monopoly(self):
        return False

    def can_play_road_builder(self):
        return False


class GameStateStealUsingKnight(GameStateSteal):
    """
    Defined as
    - AFTER the player has moved the robber using the knight
    - BEFORE the player has stolen a card using the knight
    """
    def steal(self, victim):
        self.game.catanlog.log_player_plays_dev_knight(
            self.game.get_cur_player(),
            hexgrid.location(hexgrid.TILE, self.game.robber_tile),
            victim
        )
        self.game.set_state(GameStateDuringTurnAfterRoll(self.game))


class GameStateDuringTurnAfterRoll(GameStateInGame):
    """
    The most common state.

    Defined as
    - AFTER the player's roll
    - BEFORE the player ends their turn
    """
    def can_end_turn(self):
        return True


class GameStatePlacingPiece(GameStateInGame):
    """
    - AFTER a player has selected to place a piece
    - WHILE the player is choosing where to place it
    - BEFORE the player has placed it
    """
    def __init__(self, game, piece_type):
        super(GameStatePlacingPiece, self).__init__(game)
        self.piece_type = piece_type

    def can_end_turn(self):
        return False

    def can_place_road(self):
        return self.piece_type == catan.pieces.PieceType.road

    def can_place_settlement(self):
        return self.piece_type == catan.pieces.PieceType.settlement

    def can_place_city(self):
        return self.piece_type == catan.pieces.PieceType.city

    def place_road(self, edge):
        if not self.can_place_road():
            logging.warning('Attempted to place road in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_road(edge)

    def place_settlement(self, node):
        if not self.can_place_settlement():
            logging.warning('Attempted to place settlement in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_settlement(node)

    def place_city(self, node):
        if not self.can_place_city():
            logging.warning('Attempted to place city in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        self.game.buy_city(node)

    ###

    def can_move_robber(self):
        return False

    def can_steal(self):
        return False

    def can_buy_road(self):
        return False

    def can_buy_settlement(self):
        return False

    def can_buy_city(self):
        return False

    def can_buy_dev_card(self):
        return False

    def can_trade(self):
        return False

    def can_play_knight(self):
        return False

    def can_play_monopoly(self):
        return False

    def can_play_road_builder(self):
        return False

    def can_play_victory_point(self):
        return True


class GameStatePlacingRoadBuilderPieces(GameStatePlacingPiece):
    """
    - AFTER a player has selected to build 2 road builder roads
    - WHILE the player is choosing where to place them
    - BEFORE the player has placed both of them
    """
    def __init__(self, game):
        super(GameStatePlacingRoadBuilderPieces, self).__init__(game, catan.pieces.PieceType.road)
        self.edges = list()

    def place_road(self, edge):
        if not self.can_place_road():
            logging.warning('Attempted to place road in illegal state={} with piece_type={}'.format(
                self.__class__.__name__,
                self.piece_type
            ))
        piece = catan.pieces.Piece(catan.pieces.PieceType.road, self.game.get_cur_player())
        self.game.board.place_piece(piece, edge)
        self.edges.append(edge)
        if len(self.edges) == 2:
            self.game.play_road_builder(self.edges[0], self.edges[1])
            self.game.set_state(GameStateDuringTurnAfterRoll(self.game))


class DevCardPlayabilityState(object):
    def __init__(self, game):
        self.game = game

    def can_play_dev_card(self):
        raise NotImplemented()


class DevCardNotPlayedState(DevCardPlayabilityState):
    def can_play_dev_card(self):
        return True


class DevCardPlayedState(DevCardPlayabilityState):
    def can_play_dev_card(self):
        return False


class BoardState(object):
    def __init__(self, board):
        self.board = board

    def modifiable(self):
        raise NotImplemented()


class BoardStateModifiable(BoardState):
    def modifiable(self):
        return True


class BoardStateLocked(BoardState):
    def modifiable(self):
        return False
