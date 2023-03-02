import re
import sys
import logging

from xqpuzzles.colors import Color
from xqpuzzles.xqboard import XiangqiBoard

PROGRESS = 15
ENGINE = 5


def configure_logging(level=logging.DEBUG):
    logging.basicConfig(format="%(message)s", level=level, stream=sys.stderr)
    logging.getLogger("chess").setLevel(logging.WARNING)

def log(color: str, message: str):
    logging.debug(color + message + Color.ENDC)

def log_board(board: XiangqiBoard, unicode_pieces=True):
    """ Logs the fen string and board representation
    """
    log(Color.VIOLET, board.fen)
    w_color = Color.WHITE
    b_color = Color.DARK_GREY
    sq_color = Color.BLACK
    board_str = "\n  " + str(board).replace("\n", "\n  ")
    board_str = re.sub("[a-z]", lambda p: b_color + p[0] + sq_color, board_str)
    board_str = re.sub("[A-Z]", lambda p: w_color + p[0] + sq_color, board_str)
    if unicode_pieces:
        piece_map = {
            "k": "\u2654",
            "q": "\u2655",
            "r": "\u2656",
            "b": "\u2657",
            "n": "\u2658",
            "p": "\u2659",
        }
        for p, code in piece_map.items():
            board_str = board_str.replace(p, code).replace(p.capitalize(), code)
    log(sq_color, board_str + "\n")

def log_move(turn, move, score, highlight=False):
    log_str = "%s %s => (%s)" % (Color.DARK_GREEN, turn, move)
    log_str = log_str.ljust(22 + len(Color.DARK_GREEN))

    log_str += Color.ENDC + Color.BLUE
    log_str += "  " + _score_str(score)
    if highlight:
        log_str += Color.YELLOW + "   Valid position!"
    log(Color.GREEN, log_str)

def _score_str(score) -> str:
    color = Color.WHITE
    if score.is_mate():
        sc = score.mate()
        if sc < 0:
            color = Color.DARK_GREY
        log_str = "%sMate: %s%d" % (Color.BLUE, color, sc)
    else:
        sc = score.score()
        if sc < 0:
            color = Color.DARK_GREY
        log_str = "%sCP: %s%d" % (Color.BLUE, color, sc)
    return log_str.ljust(10 + len(Color.BLUE + color)) + Color.ENDC
