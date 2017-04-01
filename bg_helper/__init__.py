import threading
import sys
import traceback
import logging
import socket
import time
import os.path
from subprocess import call
from functools import partial


LOGFILE = os.path.abspath('log--bg-helper.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOGFILE, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s: %(message)s'
))
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def run(cmd):
    """Run a shell command"""
    return call(cmd, shell=True)


def run_or_die(cmd):
    """Run a shell command or exit the system"""
    ret_code = run(cmd)
    if ret_code != 0:
        sys.exit(ret_code)


def get_logger_filenames(logger):
    """Return the filenames of a logger object"""
    return [
        handler.baseFilename
        for handler in logger.handlers
        if hasattr(handler, 'baseFilename')
    ]


def call_func(func, *args, **kwargs):
    """Call a function and pass *args and **kwargs to it; return a dict

    The following kwargs will be popped and used internally:

    - logger: logger object to use
    - verbose: if True (default), print line separator and tracebacks when caught
    """
    _logger = kwargs.pop('logger', logger)
    verbose = kwargs.pop('verbose', True)
    try:
        _logfile = get_logger_filenames(_logger)[0]
    except IndexError:
        _logfile = None

    info = {
        'func_name': getattr(func, '__name__', repr(type(func))),
        'args': repr(args),
        'kwargs': repr(kwargs),
    }

    try:
        value = func(*args, **kwargs)
        info.update({
            'status': 'ok',
            'value': value
        })
    except:
        etype, evalue, tb = sys.exc_info()
        epoch = time.time()
        info.update({
            'status': 'error',
            'traceback_string': traceback.format_exc(),
            'error_type': repr(etype),
            'error_value': repr(evalue),
            'func_doc': getattr(func, '__doc__', ''),
            'func_module': getattr(func, '__module__', ''),
            'fqdn': socket.getfqdn(),
            'time_epoch': epoch,
            'time_string': time.strftime(
                '%Y_%m%d-%a-%H%M%S', time.localtime(epoch)
            )
        })
        if verbose:
            print('=' * 70)
        _logger.error('func={} args={} kwargs={}'.format(
            info['func_name'],
            info['args'],
            info['kwargs'],
        ))
        if verbose:
            print(info['traceback_string'])
        if _logfile:
            with open(_logfile, 'a') as fp:
                fp.write(info['traceback_string'])

    return info


class SimpleBackgroundTask(object):
    """Run a single command in a background thread and log any exceptions

    You can pass a callable object, or a string representing a shell command

    - if passing a callable, you may also pass in the args and kwargs
        - since the callable will be executed by the `call_func` function,
          the `logger` and `verbose` keyword arguments (if passed in) will be
          used by `call_func`
    """
    def __init__(self, func, *args, **kwargs):
        """
        - func: callable object or string
        """
        if not callable(func):
            func = partial(run, func)
            args = ()
            kwargs = {}

        self._func = func
        self._args = args
        self._kwargs = kwargs

        # Setup the daemonized thread and start running it
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        call_func(self._func, *self._args, **self._kwargs)
