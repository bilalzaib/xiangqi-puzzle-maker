import re

try:
    import pyffish as sf
except ImportError:
    print("No pyffish module installed!")

XIANGQI_START_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'
DEFAULT_VARIANT = 'xiangqi'
RED, BLACK = 1, 2
MATE, STALEMATE, DRAW = range(1, 4)


class InvalidMove(Exception):
    pass


def uci_to_ucci(uci):
    c1, r1, c2, r2 = re.findall(r'[a-i]|[0-9]+', uci)
    return f'{c1}{int(r1) - 1}{c2}{int(r2) - 1}'


def ucci_to_uci(uci):
    c1, r1, c2, r2 = re.findall(r'[a-i]|[0-9]+', uci)
    return f'{c1}{int(r1) + 1}{c2}{int(r2) + 1}'


def fen_to_board(fen):
    fen = fen.split()[0]
    fen = re.sub(r'\d', (lambda m: ' ' * int(m.group(0))), fen)
    rows = fen.split('/')
    board = []
    for row in rows:
        board.append(list(row))

    return board


def uci_to_board_coord(uci):
    matches = re.match(r'^([a-i])(\d+)([a-i])(\d+)', uci).groups()
    c1 = ord(matches[0]) - 97
    r1 = 9 - (int(matches[1]) - 1)
    c2 = ord(matches[2]) - 97
    r2 = 9 - (int(matches[3]) - 1)

    return (r1, c1), (r2, c2)


class XiangqiBoard:

    def __init__(self, fen=XIANGQI_START_FEN, validate_fen=False, ucci=False):
        self.variant = DEFAULT_VARIANT

        if validate_fen and sf.validate_fen(fen, self.variant) != 1:
            raise AssertionError('Invalid initial fen entered')

        self.ucci = ucci
        self.initial_fen = fen
        self.fen = fen
        self.uci_stack = []

    def __str__(self):
        fen = self.fen
        if '[' in fen:
            board, rest = fen.split('[')
        else:
            board = fen.split()[0]
        board = board.replace('+', '')
        board = re.sub(r'\d', (lambda m: '.' * int(m.group(0))), board)
        board = ' '.join(list('\n' + board.replace('/', '\n')))

        return board

    @property
    def turn(self):
        return True if self.fen.split()[1] == 'w' else False

    @property
    def stack(self):
        if not self.ucci:
            return self.uci_stack

        return [uci_to_ucci(uci) for uci in self.uci_stack]

    def push(self, moves, is_ucci=False):
        """
        Apply the given move on the board

        Parameters
        ----------
        moves : List
            The list of moves that are going to be applied current fen
        """
        if is_ucci:
            moves = [ucci_to_uci(m) for m in moves]

        try:
            self.fen = sf.get_fen(self.variant, self.fen, moves)
            self.uci_stack += moves
        except Exception:
            raise InvalidMove('{} is not valid move sequence'.format(moves))

    def get_san(self, move, is_ucci=False):
        """
        Returns the SAN notation of current move
        """
        if is_ucci:
            move = ucci_to_uci(move)

        return sf.get_san(self.variant, self.fen, move, sf.NOTATION_DEFAULT)

    def legal_moves(self):
        """
        Returns the list of all available legal moves on the board
        """
        return sf.legal_moves(self.variant, self.fen, [])

    def is_checked(self):
        """
        Returns the boolean if any of the king is in check or not
        """
        return sf.gives_check(self.variant, self.fen, [])

    def insufficient_material(self):
        """
        Returns the tuple of boolean to state which player has insufficient material. i.e
        If both player has insufficient material -> (False, False)
        If red has insufficient material -> (True, False)
        """
        return sf.has_insufficient_material(self.variant, self.fen, [])

    def is_optional_game_end(self):
        return sf.is_optional_game_end(self.variant, self.fen, [])

    def game_result(self):
        return sf.game_result(self.variant, self.fen, [])

    def game_status(self):
        status = None
        if all(self.insufficient_material()):
            return DRAW

        # TODO: Need to add check for rules i.e 50 move or repetition
        legal_moves = self.legal_moves()
        if legal_moves:
            return status

        if self.is_checked():
            status = MATE
        else:
            status = STALEMATE

        return status

    def get_captured_piece(self, move, is_ucci=False):
        """
        Will return the piece which is being captured
        """
        if is_ucci:
            move = ucci_to_uci(move)

        board_2d = fen_to_board(self.fen)
        source, dest = uci_to_board_coord(move)

        return board_2d[dest[0]][dest[1]]

    def copy(self):
        board = type(self)(None)
        board.initial_fen = self.initial_fen
        board.fen = self.fen
        board.uci_stack = [m for m in self.uci_stack]
        board.ucci = self.ucci

        return board

    def print_pos(self):
        print() # noqa T001
        uni_pieces = {'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
                      'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙', '.': '·', '/': '\n'}
        fen = self.fen
        if '[' in fen:
            board, rest = fen.split('[')
        else:
            board = fen.split()[0]
        board = board.replace('+', '')
        board = re.sub(r'\d', (lambda m: '.' * int(m.group(0))), board)
        print('', ' '.join(uni_pieces.get(p, p) for p in board))    # noqa T001