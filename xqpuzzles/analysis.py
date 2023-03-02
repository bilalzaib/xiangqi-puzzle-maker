import abc
import logging
from collections import namedtuple
from typing import List

from xqpuzzles.cmd import open_process, uci, setoption, isready, kill_process, set_variant_options, send, go
from xqpuzzles.constants import MEMORY, THREADS, DEFAULT_DEPTH, DEFAULT_MOVETIME, STOCKFISH_COMMAND, STOCKFISH_DIR, \
    STOCKFISH_NNUE_FILE, PIKAFISH_COMMAND, PIKAFISH_DIR, PIKAFISH_NNUE_FILE

AnalyzedMove = namedtuple("AnalyzedMove", ["move", "move_san", "score", "pv"])


class Engine(metaclass=abc.ABCMeta):

    def __init__(self, command, engine_dir, nnue_file):
        self.engine = open_process(command, engine_dir)
        self.engine_info, _ = uci(self.engine)
        self.engine_info.pop('author', None)
        logging.info('Started %s engine, pid: %d',
                     self.engine_info.get('name', 'Engine <?>'), self.engine.pid)

        self.set_engine_options(nnue_file)
        isready(self.engine)

    @property
    def name(self):
        return self.engine_info.get('name', '<?>')

    def set_engine_options(self, nnue_file):
        # Prepare UCI options
        self.engine_info['options'] = {}
        self.engine_info['options']['threads'] = str(THREADS)
        self.engine_info['options']['hash'] = str(MEMORY)
        self.engine_info['options']['EvalFile'] = nnue_file

        # Set UCI options
        for name, value in self.engine_info['options'].items():
            setoption(self.engine, name, value)

    def quit(self):
        if not self.engine:
            return

        try:
            kill_process(self.engine)
        except OSError:
            logging.exception('Failed to kill engine process.')

    @abc.abstractmethod
    def is_ucci(self) -> bool:
        """
        Returns if the engine is using UCCI protocol or not
        """

    @abc.abstractmethod
    def analysis(self, board, depth) -> List[AnalyzedMove]:
        """
        Analyses a position and returns a dictionary of analysis infos
        """

    @abc.abstractmethod
    def best_move(self, board, depth) -> AnalyzedMove:
        """
        Will return the best move on given board position
        """


class Stockfish(Engine):

    def __init__(self):
        super().__init__(STOCKFISH_COMMAND, STOCKFISH_DIR, STOCKFISH_NNUE_FILE)

    def is_ucci(self) -> bool:
        return False

    def analysis(self, board, multipv=3) -> List[AnalyzedMove]:
        set_variant_options(self.engine, 'xiangqi')
        setoption(self.engine, 'UCI_AnalyseMode', False)
        send(self.engine, 'ucinewgame')
        isready(self.engine)

        infos = go(self.engine, board, depth=DEFAULT_DEPTH, movetime=DEFAULT_MOVETIME, multipv=multipv)
        best_moves = []
        for info in infos:
            move = info["pv"][0]
            score = info["score"].white()
            best_moves.append(AnalyzedMove(move, board.get_san(move), score, info["pv"]))

        return infos

    def best_move(self, board) -> AnalyzedMove:
        set_variant_options(self.engine, 'xiangqi')
        setoption(self.engine, 'UCI_AnalyseMode', False)
        send(self.engine, 'ucinewgame')
        isready(self.engine)

        infos = go(self.engine, board, movetime=DEFAULT_MOVETIME, depth=DEFAULT_DEPTH)
        info = infos[0]
        score = info["score"].white()
        if not info.get("pv"):
            return AnalyzedMove(None, None, score, None)

        best_move = info["pv"][0]
        return AnalyzedMove(best_move, board.get_san(best_move), score, info["pv"])


class Pikafish(Engine):

    def __init__(self):
        super().__init__(PIKAFISH_COMMAND, PIKAFISH_DIR, PIKAFISH_NNUE_FILE)

    def is_ucci(self) -> bool:
        return True

    def analysis(self, board, multipv=3) -> List[AnalyzedMove]:
        setoption(self.engine, 'UCI_WDLCentipawn', False)
        send(self.engine, 'ucinewgame')
        isready(self.engine)

        infos = go(self.engine, board, depth=DEFAULT_DEPTH, movetime=DEFAULT_MOVETIME, multipv=multipv)
        best_moves = []
        for info in infos:
            move = info["pv"][0]
            score = info["score"].white()
            best_moves.append(AnalyzedMove(move, board.get_san(move, is_ucci=board.ucci), score, info["pv"]))

        return infos

    def best_move(self, board) -> AnalyzedMove:
        setoption(self.engine, 'UCI_WDLCentipawn', False)
        send(self.engine, 'ucinewgame')
        isready(self.engine)

        infos = go(self.engine, board, movetime=DEFAULT_MOVETIME, depth=DEFAULT_DEPTH)
        info = infos[0]
        score = info["score"].white()
        if not info.get("pv"):
            return AnalyzedMove(None, None, score, None)

        best_move = info["pv"][0]
        return AnalyzedMove(best_move, board.get_san(best_move, is_ucci=board.ucci), score, info["pv"])