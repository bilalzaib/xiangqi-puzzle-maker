import csv
import os

from chess.engine import Score

from xqpuzzles.xqboard import XiangqiBoard


def sign(score: Score) -> int:
    if score.is_mate():
        s = score.mate()
    else:
        s = score.score()
    if s > 0:
        return 1
    elif s < 0:
        return -1
    return 0


def get_material_diff(board: XiangqiBoard):
    red = 0
    black = 0
    for piece in board.fen.split(' ')[0]:
        if piece in ('r', 'c', 'n', 'h'):
            black += 1
        elif piece in ('R', 'C', 'N', 'H'):
            red += 1

    return abs(red - black)


def export_puzzles_to_csv(csv_file, puzzles, game_id=None):
    # Check if the file exists
    if not os.path.isfile(csv_file):
        # If it doesn't exist, create a new file and write the header row
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['game_id', 'fen', 'moves_count', 'theme', 'score', 'first_turn', 'pv', 'url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    with open(csv_file, 'a', newline='') as f:
        fieldnames = ['game_id', 'fen', 'moves_count', 'theme', 'score', 'first_turn', 'pv', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        for puzzle in puzzles:
            row = {
                'game_id': game_id,
                'fen': puzzle['fen'],
                'moves_count': puzzle['moves_count'],
                'theme': puzzle['theme'],
                'score': puzzle['score'],
                'first_turn': puzzle['first_turn'],
                'pv': puzzle['pv'],
                'url': f'https://xiangqi-dev.arbisoft.com/editor/{puzzle["fen"].split()[0]}',
            }
            writer.writerow(row)
