import threading
import sys
import traceback
import socket
import time
import subprocess
import uuid
import fs_helper as fh
from functools import partial
from os import remove


logger = fh.get_logger(__name__)


def run(cmd, stderr_to_stdout=False, debug=False, timeout=None, exception=False, show=False):
    """Run a shell command and return the exit status

    - cmd: string with shell command
    - stderr_to_stdout: if True, redirect stderr to stdout
    - debug: if True, insert breakpoint right before subprocess.call
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if non-zero exit status or TimeoutExpired
    - show: if True, show the command before executing
    """
    ret_code = 1
    if show:
        print('\n$ {}'.format(cmd))

    try:
        if stderr_to_stdout:
            if debug:
                breakpoint()
            ret_code = subprocess.call(cmd, stderr=sys.stdout.buffer, timeout=timeout, shell=True)
            if exception and ret_code != 0:
                raise Exception("The return code was {} (not 0) for {}".format(ret_code, repr(cmd)))
        else:
            # Annoying that you can't just use an io.StringIO() instance for error_buf
            error_buffer_path = '/tmp/error-buffer-{}.txt'.format(str(uuid.uuid4()))
            with open(error_buffer_path, 'w') as error_buf:
                if debug:
                    breakpoint()
                ret_code = subprocess.call(cmd, stderr=error_buf, timeout=timeout, shell=True)
            if exception:
                with open(error_buffer_path, 'r') as fp:
                    text = fp.read()
                    if text != '':
                        # This section might grow if more commands write non-errors to stderr
                        if 'git' in cmd:
                            if 'fatal:' in text:
                                raise Exception(text.strip())
                        else:
                            raise Exception(text.strip())
            remove(error_buffer_path)
    except subprocess.TimeoutExpired as e:
        if exception:
            output = 'Timeout of {} reached when running: {}'.format(timeout, cmd)
            raise Exception(output.strip())
    return ret_code


def run_output(cmd, strip=True, debug=False, timeout=None, exception=False, show=False):
    """Run a shell command and return output or error

    - cmd: string with shell command
    - strip: if True, strip trailing and leading whitespace from output
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if CalledProcessError or TimeoutExpired
    - show: if True, show the command before executing
    """
    if show:
        print('\n$ {}'.format(cmd))
    try:
        if debug:
            breakpoint()
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, timeout=timeout)
    except subprocess.CalledProcessError as e:
        output = e.output
        if exception:
            from pprint import pprint
            pprint(sys.exc_info())
            raise Exception(output.decode('utf-8').strip())
    except subprocess.TimeoutExpired:
        output = 'Timeout of {} reached when running: {}'.format(timeout, cmd).encode('utf-8')
        if exception:
            raise Exception(output.decode('utf-8').strip())
    if exception:
        output = output.decode('utf-8').strip()
        if 'git' in cmd and 'fatal:' in output:
            raise Exception(output)
        output = output.encode('utf-8')

    output = output.decode('utf-8')
    if strip:
        output = output.strip()
    return output


def run_or_die(cmd, stderr_to_stdout=False, debug=False, timeout=None, exception=True, show=False):
    """Run a shell command; if non-success, raise Exception or exit the system

    - cmd: string with shell command
    - stderr_to_stdout: if True, redirect stderr to stdout
    - debug: if True, insert breakpoint right before subprocess.call
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if return code of cmd is non-zero
        - otherwise, do system exit if return code of cmd is non-zero
    - show: if True, show the command before executing
    """
    try:
        ret_code = run(cmd, stderr_to_stdout=stderr_to_stdout, debug=debug, timeout=timeout, exception=exception, show=show)
    except:
        if exception:
            raise
        else:
            sys.exit(1)
    else:
        if ret_code != 0:
            if exception:
                raise Exception
            else:
                sys.exit(ret_code)


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
        _logfile = fh.get_logger_filenames(_logger)[0]
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
