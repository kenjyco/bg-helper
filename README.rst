Install
-------

::

   % pip3 install bg-helper

Usage
-----

   ``import bg_helper as bh``

Helper functions in ``bg_helper`` that can be used to:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  run shell commands in a variety of ways

   ::

      run(cmd, debug=False, timeout=None, exception=False, show=False)
          Run a shell command and return the exit status

          - cmd: string with shell command
          - debug: if True, insert breakpoint right before subprocess.call
          - timeout: number of seconds to wait before stopping cmd
          - exception: if True, raise Exception if non-zero exit status or TimeoutExpired
          - show: if True, show the command before executing

      run_output(cmd, debug=False, timeout=None, exception=False, show=False)
          Run a shell command and return output or error

          - cmd: string with shell command
          - debug: if True, insert breakpoint right before subprocess.call
          - timeout: number of seconds to wait before stopping cmd
          - exception: if True, raise Exception if non-zero exit status or TimeoutExpired
          - show: if True, show the command before executing

      run_or_die()
          Run a shell command; if non-success, raise Exception or exit the system

          - cmd: string with shell command
          - debug: if True, insert breakpoint right before subprocess.call
          - timeout: number of seconds to wait before stopping cmd
          - exception: if True, raise Exception if non-zero exit status or TimeoutExpired
          - show: if True, show the command before executing

-  call a Python function & capture the value or any uncaught exceptions

   ::

      call_func(func, *args, **kwargs)
          Call a func with arbitrary args/kwargs and capture uncaught exceptions

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

-  start a long-running shell command or Python function in the
   background (like ``vlc`` media player)

   ::

      SimpleBackgroundTask(func, *args, **kwargs)
          Run a single command in a background thread and log any exceptions

          You can pass a callable object, or a string representing a shell command

          - if passing a callable, you may also pass in the args and kwargs
              - since the callable will be executed by the `call_func` function,
                  the `logger` and `verbose` keyword arguments (if passed in) will be
                  used by `call_func`

Helper functions in ``bg_helper.tools``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

grep
^^^^

-  ``grep_output``

ps
^^

-  ``ps_output``

docker
^^^^^^

-  ``docker_ok``
-  ``docker_stop``
-  ``docker_start_or_run``
-  ``docker_container_id``
-  ``docker_container_inspect``
-  ``docker_container_config``
-  ``docker_container_env_vars``
-  ``docker_logs``
-  ``docker_exec``
-  ``docker_exec_wait``
-  ``docker_shell``
-  ``docker_cleanup_volumes``
-  ``docker_redis_start``
-  ``docker_redis_cli``
-  ``docker_mongo_start``
-  ``docker_mongo_cli``
-  ``docker_postgres_start``
-  ``docker_postgres_cli``
-  ``docker_postgres_wait``
-  ``docker_mysql_start``
-  ``docker_mysql_cli``
-  ``docker_mysql_wait``
-  ``docker_alpine_start``
-  ``docker_ubuntu_start``
-  ``docker_fedora_start``

Examples
--------

::

   % ipython
   ...

   In [1]: import bg_helper as bh

   In [2]: def lame():
      ...:     return 1/0

   In [3]: def blah(*args, **kwargs):
      ...:     return locals()

   In [4]: bh.call_func(blah)
   Out[4]: 
   {'args': '()',
    'func_name': 'blah',
    'kwargs': '{}',
    'status': 'ok',
    'value': {'args': (), 'kwargs': {}}}

   In [5]: bh.call_func(blah, 'cats', 'dogs')
   Out[5]: 
   {'args': "('cats', 'dogs')",
    'func_name': 'blah',
    'kwargs': '{}',
    'status': 'ok',
    'value': {'args': ('cats', 'dogs'), 'kwargs': {}}}

   In [6]: bh.call_func(blah, 'cats', 'dogs', meh=[1, 2, 3, 4, 5])
   Out[6]: 
   {'args': "('cats', 'dogs')",
    'func_name': 'blah',
    'kwargs': "{'meh': [1, 2, 3, 4, 5]}",
    'status': 'ok',
    'value': {'args': ('cats', 'dogs'), 'kwargs': {'meh': [1, 2, 3, 4, 5]}}}

   In [7]: bh.call_func(lame)
   ======================================================================
   2017-04-01 12:32:35,107: func=lame args=() kwargs={}
   Traceback (most recent call last):
     File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func
       value = func(*args, **kwargs)
     File "<ipython-input-2-ac0fa5de647a>", line 2, in lame
       return 1/0
   ZeroDivisionError: division by zero

   Out[7]: 
   {'args': '()',
    'error_type': "<class 'ZeroDivisionError'>",
    'error_value': "ZeroDivisionError('division by zero',)",
    'fqdn': 'x200-purple',
    'func_doc': None,
    'func_module': '__main__',
    'func_name': 'lame',
    'kwargs': '{}',
    'status': 'error',
    'time_epoch': 1491067955.1004958,
    'time_string': '2017_0401-Sat-123235',
    'traceback_string': 'Traceback (most recent call last):\n  File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func\n    value = func(*args, **kwargs)\n  File "<ipython-input-2-ac0fa5de647a>", line 2, in lame\n    return 1/0\nZeroDivisionError: division by zero\n'}

   In [8]: cat log--bg-helper.log
   2017-04-01 12:32:35,107 - ERROR - call_func: func=lame args=() kwargs={}
   Traceback (most recent call last):
     File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func
       value = func(*args, **kwargs)
     File "<ipython-input-2-ac0fa5de647a>", line 2, in lame
       return 1/0
   ZeroDivisionError: division by zero

   In [9]: bh.SimpleBackgroundTask('echo "hello from console" > /tmp/blahblah.txt')
   Out[9]: <bg_helper.SimpleBackgroundTask at 0x7ff112229c18>

   In [10]: ls /tmp/blahblah.txt
   /tmp/blahblah.txt

   In [11]: cat /tmp/blahblah.txt
   hello from console

   In [12]: bh.SimpleBackgroundTask('echo "$(date)" >> /tmp/blahblah.txt')
   Out[12]: <bg_helper.SimpleBackgroundTask at 0x7ff110057cf8>

   In [13]: cat /tmp/blahblah.txt
   hello from console
   Sat Apr  1 12:33:23 CDT 2017
