#!/usr/bin/env python3

""" Creates Xiangqi puzzles from CSV file or given uci moves
"""

import argparse
import ast
import csv
import logging
import sys

from xqpuzzles.colors import Color
from xqpuzzles.logger import configure_logging, log
from xqpuzzles.logger import ENGINE
from xqpuzzles.puzzle_finder import find_puzzle_candidates
from xqpuzzles.analysis import Stockfish, Pikafish
from xqpuzzles.utils import export_puzzles_to_csv

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Data inputs
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--moves", metavar="MOVES", type=str,
                    help="UCI moves of a xiangqi game")
group.add_argument("--games_csv", metavar="GAMES_CSV", type=str,
                    help="A CSV file with games to scan for puzzles")

# Misc settings
parser.add_argument("--engine", metavar="ENGINE", type=str, choices=['pikafish', 'stockfish'],
                    help="Give a valid engine name ('pikafish', 'stockfish')", default='pikafish')
parser.add_argument("--quiet", default=False, action="store_true",
                    help="substantially reduce the number of logged messages")
parser.add_argument("--scan-only", default=False, action="store_true",
                    help="Only scan for possible puzzles. Don't analyze positions")

print(sys.argv)
if len(sys.argv) < 2:
    parser.print_usage()
    sys.exit(0)

settings = parser.parse_args()
try:
    # Optionally fix colors on Windows and in journals if the colorama module
    # is available.
    import colorama
    wrapper = colorama.AnsiToWin32(sys.stdout)
    if wrapper.should_wrap():
        sys.stdout = wrapper.stream
except ImportError:
    pass

if settings.quiet:
    configure_logging(level=logging.INFO)
else:
    configure_logging(level=logging.DEBUG)
    # configure_logging(level=ENGINE)


engine_map = {'pikafish': Pikafish, 'stockfish': Stockfish}
engine = engine_map[settings.engine]()

# Try to generate puzzle positions from given UCI moves
if settings.moves:
    try:
        game_moves = settings.moves.split(',')
        log(Color.DIM, engine.name)
        log(Color.DARK_BLUE, str(game_moves))

        puzzles = find_puzzle_candidates(engine, game_moves)

        log(Color.YELLOW, "# Found valid puzzle positions: %d" % len(puzzles))

        # TODO: Remove this code
        with open('output.csv', 'w', newline='') as csvfile:
            fieldnames = ['game_id', 'url', 'fen', 'theme', 'score', 'first_turn', 'pv']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            export_puzzles_to_csv(writer, puzzles)

            for puzzle in puzzles:
                url = f'https://xiangqi-dev.arbisoft.com/editor/{puzzle["fen"].split()[0]}'
                log(Color.UNDERLINE, f'Position: {url}')

        engine.quit()
        exit(0)
    except Exception as exp:
        logging.exception(exp)
        engine.quit()
        exit(0)

log(Color.DIM, engine.name)

with open(settings.games_csv, 'r') as file:
    reader = csv.DictReader(file)

    out_file = settings.games_csv.split('.')[0]
    with open(f'{out_file}_out.csv', 'w', newline='') as csvfile:
        fieldnames = ['game_id', 'url', 'fen', 'theme', 'score', 'first_turn', 'pv']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for game in reader:
            try:
                game_moves = ast.literal_eval(game['moves'])
                log(Color.DARK_BLUE, str(game_moves))
                puzzles = find_puzzle_candidates(engine, game_moves, skip_initial=10)
                export_puzzles_to_csv(writer, puzzles, game_id=game['id'])

                log(Color.YELLOW, f"Found {len(puzzles)} valid positions from game ID {game['id']}")
                for puzzle in puzzles:
                    log(Color.BOLD, f'First Turn ==> {puzzle["first_turn"]}')
                    url = f'https://xiangqi-dev.arbisoft.com/editor/{puzzle["fen"].split()[0]}'
                    log(Color.UNDERLINE, url)

            except Exception as exp:
                logging.info(f'Got exception in game: {game["id"]}')
                logging.exception(exp)

engine.quit()
