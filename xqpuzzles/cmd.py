import logging
import os
import signal
import subprocess
import threading

from chess.engine import InfoDict, Info, INFO_ALL, INFO_PV, INFO_SCORE, Cp, Mate, PovScore

from xqpuzzles.xqboard import XiangqiBoard
from xqpuzzles.logger import ENGINE


def open_process(command, cwd=None, shell=True, _popen_lock=threading.Lock()):
    kwargs = {
        'shell': shell,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'stdin': subprocess.PIPE,
        'bufsize': 1,  # Line buffered
        'universal_newlines': True,
    }

    if cwd is not None:
        kwargs['cwd'] = cwd

    # Prevent signal propagation from parent process
    try:
        # Windows
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    except AttributeError:
        # Unix
        kwargs['preexec_fn'] = os.setpgrp

    with _popen_lock:  # Work around Python 2 Popen race condition
        return subprocess.Popen(command, **kwargs)


def kill_process(p):
    try:
        # Windows
        p.send_signal(signal.CTRL_BREAK_EVENT)
    except AttributeError:
        # Unix
        os.killpg(p.pid, signal.SIGKILL)

    p.communicate()


def send(p, line):
    logging.log(ENGINE, '%s << %s', p.pid, line)
    p.stdin.write(line + '\n')
    p.stdin.flush()


def recv(p):
    while True:
        line = p.stdout.readline()
        if line == '':
            raise EOFError()

        line = line.rstrip()

        logging.log(ENGINE, '%s >> %s', p.pid, line)

        if line:
            return line


def recv_uci(p):
    command_and_args = recv(p).split(None, 1)
    if len(command_and_args) == 1:
        return command_and_args[0], ''
    elif len(command_and_args) == 2:
        return command_and_args


def uci(p):
    send(p, 'uci')

    engine_info = {}
    variants = set()

    while True:
        command, arg = recv_uci(p)

        if command == 'uciok':
            return engine_info, variants
        elif command == 'id':
            name_and_value = arg.split(None, 1)
            if len(name_and_value) == 2:
                engine_info[name_and_value[0]] = name_and_value[1]
        elif command == 'option':
            if arg.startswith('name UCI_Variant type combo default chess'):
                for variant in arg.split(' ')[6:]:
                    if variant != 'var':
                        variants.add(variant)
        elif command == 'Fairy-Stockfish' and ' by ' in arg:
            # Ignore identification line
            pass
        else:
            logging.warning('Unexpected engine response to uci: %s %s', command, arg)


def isready(p):
    send(p, 'isready')
    while True:
        command, arg = recv_uci(p)
        if command == 'readyok':
            return True
        elif command == 'info' and arg.startswith('string '):
            pass
        else:
            logging.warning('Unexpected engine response to isready: %s %s', command, arg)


def setoption(p, name, value):
    if value is True:
        value = 'true'
    elif value is False:
        value = 'false'
    elif value is None:
        value = 'none'

    send(p, 'setoption name %s value %s' % (name, value))


def _parse_uci_info(arg: str, root_board: XiangqiBoard, selector: Info = INFO_ALL) -> InfoDict:
    info = InfoDict({})  # type: InfoDict
    if not selector:
        return info

    # Initialize parser state.
    pv = None  # type: Optional[List[str]]
    score_kind = None
    string = []  # type: List[str]

    # Parameters with variable length can only be handled when the
    # next parameter starts or at the end of the line.
    def end_of_parameter() -> None:
        if pv is not None:
            info["pv"] = pv

    # Parse all other parameters.
    current_parameter = None
    for token in arg.split(" "):
        if current_parameter == "string":
            string.append(token)
        elif not token:
            # Ignore extra spaces. Those can not be directly discarded,
            # because they may occur in the string parameter.
            pass
        elif token in ["depth", "seldepth", "time", "nodes", "pv", "multipv",
                       "score", "currmove", "currmovenumber", "hashfull",
                       "nps", "tbhits", "cpuload", "refutation", "currline",
                       "ebf", "string"]:
            end_of_parameter()
            current_parameter = token

            pv = None
            score_kind = None

            if current_parameter == "pv" and selector & INFO_PV:
                pv = []
        elif current_parameter in ["depth", "seldepth", "nodes", "multipv", "currmovenumber", "hashfull", "nps", "tbhits", "cpuload"]:
            try:
                info[current_parameter] = int(token)
            except ValueError:
                logging.error("exception parsing %s from info: %r", current_parameter, arg)
        elif current_parameter == "time":
            try:
                info[current_parameter] = int(token) / 1000.0
            except ValueError:
                logging.error("exception parsing %s from info: %r", current_parameter, arg)
        elif current_parameter == "pv" and pv is not None:
            try:
                pv.append(token)
            except ValueError:
                logging.exception("exception parsing pv from info: %r, position at root: %s", arg, root_board.fen())
        elif current_parameter == "score" and selector & INFO_SCORE:
            try:
                if token in ["cp", "mate"]:
                    score_kind = token
                elif token == "lowerbound":
                    info["lowerbound"] = True
                elif token == "upperbound":
                    info["upperbound"] = True
                elif score_kind == "cp":
                    info["score"] = PovScore(Cp(int(token)), root_board.turn)
                elif score_kind == "mate":
                    info["score"] = PovScore(Mate(int(token)), root_board.turn)
            except ValueError:
                logging.error("exception parsing score %s from info: %r", score_kind, arg)

    end_of_parameter()

    if string:
        info["string"] = " ".join(string)

    return info



def go(p, board: XiangqiBoard, movetime=None, clock=None, depth=None, nodes=None, multipv=1):
    setoption(p, 'MultiPV', multipv)
    send(p, 'position fen %s moves %s' % (board.initial_fen, ' '.join(board.stack)))

    builder = []
    builder.append('go')
    if movetime is not None:
        builder.append('movetime')
        builder.append(str(movetime))
    if depth is not None:
        builder.append('depth')
        builder.append(str(depth))
    if nodes is not None:
        builder.append('nodes')
        builder.append(str(nodes))
    if clock is not None:
        builder.append('wtime')
        builder.append(str(clock['wtime'] * 10))
        builder.append('btime')
        builder.append(str(clock['btime'] * 10))
        builder.append('winc')
        builder.append(str(clock['inc'] * 1000))
        builder.append('binc')
        builder.append(str(clock['inc'] * 1000))

    send(p, ' '.join(builder))

    pv_infos = [dict() for _ in range(multipv)]
    pv_infos[0]['bestmove'] = None

    while True:
        command, arg = recv_uci(p)

        if command == 'bestmove':
            bestmove = arg.split()[0]
            if bestmove and bestmove != '(none)':
                pv_infos[0]['bestmove'] = bestmove

            pv_infos = [p for p in pv_infos if p.get('score')]
            return pv_infos

        elif command == 'info':
            arg = arg or ''
            info = _parse_uci_info(arg, board)

            multipv = info.get('multipv', 1)
            pv_infos[multipv - 1].update(info)
        else:
            logging.warning('Unexpected engine response to go: %s %s', command, arg)


def set_variant_options(p, variant, chess960=False):
    variant = variant.lower()

    setoption(p, 'UCI_Chess960', chess960)
    setoption(p, 'UCI_Variant', variant)
