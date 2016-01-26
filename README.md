catan
-----

Package catan provides models for representing and manipulating a game of catan

Board coordinates must be specified as described in module [`hexgrid`](https://github.com/rosshamish/hexgrid).

`.catan` files will be written to the working directory by class Game (see [`catanlog`](https://github.com/rosshamish/catanlog)).

class Game also supports undo and redo, which is useful for building GUIs.

Supports Python 3. Might work in Python 2.

> Author: Ross Anderson ([rosshamish](https://github.com/rosshamish))

### Installation

```
pip install catan
```

### Usage

```
import catan.board
import catan.game
import catan.trading

players = [Player(1, 'ross', 'red'),
           Player(2, 'josh', 'blue'),
           Player(3, 'yuri', 'green'),
           Player(4, 'zach', 'orange')]
board = catan.board.Board()
game = catan.game.Game(board=board)

game.start(players=players)
print(game.get_cur_player())  # -> ross (red)
game.buy_settlement(0x37)
game.buy_road(0x37)
game.end_turn()
...
game.roll(6)
game.trade(trade=catan.trading.CatanTrade(...))
game.undo()
game.redo()
game.play_knight(...)
game.end_turn()
...
game.end()
```

See [`catan-spectator`](https://github.com/rosshamish/catan-spectator) for extensive usage.

### File Format

<!-- remember to update this section in sync with "File Format" in github.com/rosshamish/catan-spectator/README.md -->

catan-spectator writes game logs in the `.catan` format described by package [`catanlog`](https://github.com/rosshamish/catanlog).

They look like this:

```
green rolls 6
blue buys settlement, builds at (1 NW)
orange buys city, builds at (1 SE)
red plays dev card: monopoly on ore
```

### Documentation

Most classes and modules are documented. Read the docstrings! If something is confusing or missing, open an issue.

### License

GPLv3
