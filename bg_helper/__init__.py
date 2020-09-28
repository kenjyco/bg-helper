import threading
import sys
import traceback
import socket
import time
import subprocess
import fs_helper as fh
from functools import partial


logger = fh.get_logger(__name__)


def run(cmd, show=False):
    """Run a shell command and return the exit status

    - show: if True, show the command before executing
    """
    if show:
        print('\n$ {}'.format(cmd))
    return subprocess.call(cmd, shell=True)


def run_output(cmd, timeout=None, show=False):
    """Run a shell command and return output or error

    - timeout: number of seconds to wait before stopping cmd
    - show: if True, show the command before executing
    """
    if show:
        print('\n$ {}'.format(cmd))
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, timeout=timeout)
    except subprocess.CalledProcessError as e:
        output = e.output
    except subprocess.TimeoutExpired:
        output = 'Timeout of {} reached when running: {}'.format(timeout, cmd).encode('utf-8')
    return output.decode('utf-8').strip()


def run_or_die(cmd, exception=True, show=False):
    """Run a shell command; if non-success, raise Exception or exit the system

    - exception: if True, raise an exception (otherwise, do system exit)
    - show: if True, show the command before executing
    """
    ret_code = run(cmd, show=show)
    if ret_code != 0:
        if exception:
            raise Exception
        else:
            sys.exit(ret_code)


def get_logger_filenames(logger):
    """Return the filenames of a logger object"""
    return [
        handler.baseFilename
        for handler in logger.handlers
        if hasattr(handler, 'baseFilename')
    ]


def call_func(func, *args, **kwargs):
    """Call a func with arbitrary args/kwargs and capture uncaught exceptions

    The following kwargs will be popped and used internally:

    - logger: logger object to use
    - verbose: if True (default), print line separator & tracebacks when caught

    The returned dict will always have at least the following keys:

    - `func_name`
    - `args`
    - `kwargs`
    - `status` (ok/error)

    If the function call was successful, there will also be a `value` key. If
    there was an uncaught exception, the following additional keys will be
    provided in the return dict

    - `error_type`
    - `error_value`
    - `fqdn`
    - `func_doc`
    - `func_module`
    - `time_epoch`
    - `time_string`
    - `traceback_string`
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


from bg_helper import tools
