from chess.engine import Score

from xqpuzzles.logger import log, log_move
from xqpuzzles.colors import Color
from xqpuzzles.constants import DEFAULT_DEPTH
from xqpuzzles.xqboard import XiangqiBoard


def find_puzzle_candidates(engine, moves, scan_depth=DEFAULT_DEPTH, skip_initial=5):
    """
    finds puzzle candidates from a xiangqi game
    """
    log(Color.DIM, "Scanning game moves for puzzles (depth: %d)..." % scan_depth)
    puzzles = []

    board = XiangqiBoard(ucci=engine.is_ucci())
    board.push(moves[:skip_initial])

    prev_score = engine.best_move(board).score

    for move in moves[skip_initial:]:
        next_board = board.copy()
        next_board.push([move])

        cur_analysis = engine.best_move(next_board)
        cur_score = cur_analysis.score

        turn = 'RED' if next_board.turn else 'BLACK'
        highlight_move = False
        if is_capturing_pos(prev_score, cur_score, next_board) or is_mate_pos(cur_score, next_board):
            highlight_move = True
            puzzle = {
                'first_turn': turn,
                'pv': cur_analysis.pv,
                'fen': next_board.fen,
                'score': cur_score,
                'theme': get_theme(next_board, cur_analysis),
            }
            puzzles.append(puzzle)

        log_move(turn, move, cur_score, highlight=highlight_move)
        prev_score = cur_score
        board = next_board

    return puzzles


def is_mate_pos(a: Score, board) -> bool:
    if not a.is_mate():
        return False

    mate = a.mate() * (1 if board.turn else -1)
    if 0 < mate <= 10:
        return True

    return False


def is_capturing_pos(a: Score, b: Score, b_board) -> bool:
    """
    Find if a given position could be capturing puzzle or not
    """
    a_cp = a.score()
    b_cp = b.score()

    if a_cp is None or b_cp is None:
        return False

    b_sign = 1 if b_board.turn else -1
    if abs(b_cp - a_cp) >= 300 and 300 < (b_sign * b_cp) <= 1500:
        return True

    return False


def get_theme(board, analysis):
    if analysis.score.is_mate():
        return 'CHECKMATE'

    # TODO: the puzzles could be Capturing if it the sequence of moves can capture any main pieces
    # otherwise, it'll be considered as mid-game puzzle
    return 'CAPTURING'
