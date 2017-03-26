import threading
import sys
import traceback
import logging
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


class SimpleBackgroundTask(object):
    """Run a single command in a background thread

    Just initialize with the function and any args/kwargs. The background
    thread is started right away and any exceptions raised will be logged
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
        try:
            self._func(*self._args, **self._kwargs)
        except:
            logger.error('func={} args={} kwargs={}'.format(
                getattr(self._func, '__name__', type(self._func)),
                repr(self._args),
                repr(self._kwargs),
            ))
            with open(LOGFILE, 'a') as fp:
                fp.write(traceback.format_exc())
