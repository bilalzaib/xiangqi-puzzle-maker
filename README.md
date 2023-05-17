# xiangqi-puzzle-maker
This is a command-line program that creates xiangqi puzzle positions from games where player made mistakes. It looks for positions where a player can:

* Checkmate the opponent in a forced sequence
* Capture an opponent piece to get a material advantage

Give it a CSV file with any number of games and it will look for positions that can be used as puzzle:

`python puzzle_maker.py --games_csv "david-games.csv" --out-csv "david-puzzles.csv"`
(_out-csv_ param is the name of the file where puzzles will be saved)

Or give it a list of moves of game, and it will try to find valid puzzle positions:

`python puzzle_maker.py --moves "h3h7,b8e8,b1c3,g7g6,c4c5,h10g8,c1e3,g8f6,b3b7,b10c8,h7c7,h8g8,d1e2,g6g5,a1d1,g5g4,h1i3,g4f4,c5c6,a10b10,e4e5,f4e4,c6b6,e4e3,d1d6,f6h5,d6d5,h5f4,c3e4,g8h8,g1e3,h8h3,i1h1,h3h5,d5d9,i10h10,h1g1,h5h4,g1g4,e8e5,e4c5,f4e6,d9d6,h4h5,g4h4,e6g5,d6f6,c10e8,h4g4,g5e6,c5e6,e7e6,f6e6,e5d5,g4g5,d5d9,g5d5,d9e9,c7a7,e9e6,d5e5,e6d6,e5e6,d6d9,e6e5,d9e9,b7e7,e9e7,a7c7,b10b6,c7c4,b6b1,e2d1,h5h4,e5e4,h4c4,i4i5,c4c1,e1e2,b1b2"`

For a list of options:

`python puzzle_maker.py -h`

## Requirements

This requires Python 3 and a UCI-compatible chess engine such as [Pikafish](https://github.com/PikaCat-OuO/Pikafish) or [Fairy-Stockfish](https://github.com/ianfab/Fairy-Stockfish/).

Create a python virtual environment (not necessary) and then install the required python libraries:

`pip install -r requirements.txt`

Make sure you have a version of Pikafish or Fairy-Stockfish available in your local directory:

* You can install a latest Pikafish binary from [here](https://github.com/official-pikafish/Pikafish/releases/tag/Pikafish-2023-02-16)
* Or download the [Fairy-Stockfish](https://github.com/ianfab/Fairy-Stockfish/) from github

And update the required engine params in `xqpuzzles/local.py` file. 
```
# PIKAFISH
PIKAFISH_DIR = 'path-to-folder'
PIKAFISH_COMMAND = './stockfish-x86_64'
PIKAFISH_NNUE_FILE = 'absolute-nnue-file-path'
```

Please see other engine params in `xqpuzzles/constants.py` and their values can be override in `xqpuzzles/local.py`

### Fetch Games Xiangi.com
To fetch games of a particular user from xiangqi.com, open `fetch_xq_games.py` file and update the required values i.e `JWT` and `user` there.

To get user games run: `python fetch_xq_games.py`, it will generate a _CSV_ file with the given user. See details in comments of _fetch_xq_games.py_ file 
