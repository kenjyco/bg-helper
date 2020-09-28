
## Install

```
% pip3 install bg-helper
```

## Usage

> `import bg_helper as bh`

### Helper functions in `bg_helper` that can be used to:

- run shell commands in a variety of ways

    ```
    run(cmd, show=False)
        Run a shell command and return the exit status

        - show: if True, show the command before executing

    run_output(cmd, timeout=None, show=False)
        Run a shell command and return output or error

        - timeout: number of seconds to wait before stopping cmd
        - show: if True, show the command before executing

    run_or_die(cmd, exception=True, show=False)
        Run a shell command; if non-success, raise Exception or exit the system

        - exception: if True, raise an exception (otherwise, do system exit)
        - show: if True, show the command before executing
    ```
- call a Python function & capture the value or any uncaught exceptions

    ```
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
    ```
- start a long-running shell command or Python function in the background (like
  `vlc` media player)

    ```
    SimpleBackgroundTask(func, *args, **kwargs)
        Run a single command in a background thread and log any exceptions

        You can pass a callable object, or a string representing a shell command

        - if passing a callable, you may also pass in the args and kwargs
            - since the callable will be executed by the `call_func` function,
                the `logger` and `verbose` keyword arguments (if passed in) will be
                used by `call_func`
    ```

### Helper functions in `bg_helper.tools` that use docker if it is installed:

- start database containers and access the db shells they contain

    ```
    docker_redis_start(name, version='6-alpine', port=6300, data_dir=None,
                       aof=True, rm=False, exception=False, show=False, force=False)
        Start or create redis container

        - name: name for the container
        - version: redis image version
        - port: port to map into the container
        - data_dir: directory that will map to container's /data
            - specify absolute path or subdirectory of current directory
        - aof: if True, use appendonly.aof file
        - rm: if True, automatically delete the container when it exits
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output
        - force: if True, stop the container and remove it before re-creating

        See: https://hub.docker.com/_/redis for image versions ("supported tags")

    docker_redis_cli(name, show=False)
        Start redis-cli on an existing container (will be started if stopped)

        - show: if True, show the docker command and output

    docker_mongo_start(name, version='4.4', port=27000, username='mongouser',
                       password='some.pass', data_dir=None, rm=False,
                       exception=False, show=False, force=False)
        Start or create mongo container

        - name: name for the container
        - version: mongo image version
        - port: port to map into the container
        - username: username to set for root user on first run
        - password: password to set for root user on first run
        - data_dir: directory that will map to container's /data/db
            - specify absolute path or subdirectory of current directory
        - rm: if True, automatically delete the container when it exits
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output
        - force: if True, stop the container and remove it before re-creating

        See: https://hub.docker.com/_/mongo for image versions ("supported tags")

    docker_mongo_cli(name, show=False)
        Start mongo on an existing container (will be started if stopped)

        - show: if True, show the docker command and output

    docker_postgres_start(name, version='13-alpine', port=5400,
                          username='postgresuser', password='some.pass',
                          db='postgresdb', data_dir=None, rm=False, exception=False,
                          show=False, force=False)
        Start or create postgres container

        - name: name for the container
        - version: postgres image version
        - port: port to map into the container
        - username: username to set as superuser on first run
        - password: password to set for superuser on first run
        - db: name of default database
        - data_dir: directory that will map to container's /var/lib/postgresql/data
            - specify absolute path or subdirectory of current directory
        - rm: if True, automatically delete the container when it exits
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output
        - force: if True, stop the container and remove it before re-creating

        See: https://hub.docker.com/_/postgres for image versions ("supported tags")

    docker_postgres_cli(name, show=False)
        Start psql on an existing container (will be started if stopped)

        - show: if True, show the docker command and output

    docker_mysql_start(name, version='8.0', port=3300, root_password='root.pass',
                       username='mysqluser', password='some.pass', db='mysqldb',
                       data_dir=None, rm=False, exception=False, show=False, force=False)
        Start or create postgres container

        - name: name for the container
        - version: mysql image version
        - port: port to map into the container
        - root_password: password to set for the root superuser account
        - username: username to set as superuser on first run
        - password: password to set for superuser on first run
        - db: name of default database
        - data_dir: directory that will map to container's /var/lib/mysql
            - specify absolute path or subdirectory of current directory
        - rm: if True, automatically delete the container when it exits
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output
        - force: if True, stop the container and remove it before re-creating

        See: https://hub.docker.com/_/mysql for image versions ("supported tags")

    docker_mysql_cli(name, show=False)
        Start mysql on an existing container (will be started if stopped)

        - show: if True, show the docker command and output
    ```
- basic wrappers (used in the database helpers above)

    ```
    docker_ok(exception=False)
        Return True if docker is available and the docker daemon is running

        - exception: if True and docker not available, raise an exception

    docker_stop(name, kill=False, signal='KILL', rm=False, exception=False, show=False)
        Return True if successfully stopped

        - name: name of the container
        - kill: if True, kill the container instead of stopping
        - signal: signal to send to the container if kill is True
        - rm: if True, remove the container after stop/kill
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output

    docker_start_or_run(name, image='', command='', detach=True, rm=False,
                        interactive=False, ports='', volumes='', env_vars={},
                        exception=False, show=False, force=False)
        Start existing container or create/run container

        - name: name for the container
        - image: image to use (i.e. image:tag)
        - command: command to run in the comtainer
        - detach: if True, run comtainer in the background
            - if interactive is True, detach will be set to False
        - rm: if True, automatically delete the container when it exits
        - interactive: if True, keep STDIN open and allocate pseudo-TTY
        - ports: string containing {host-port}:{container-port} pairs separated by
        one of , ; |
        - volumes: string containing {host-path}:{container-path} pairs separated by
        one of , ; |
        - env_vars: a dict of environment variables and values to set
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker commands and output
        - force: if True, stop the container and remove it before re-creating

    docker_container_id(name)
        Return the container ID for running container name

    docker_container_inspect(name, exception=False, show=False)
        Return detailed information on specified container as a list

        - name: name of the container
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker command and output

    docker_container_config(name, exception=False, show=False)
        Return dict of config information for specified container (from inspect)

        - name: name of the container
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker command and output

    docker_container_env_vars(name, exception=False, show=False)
        Return dict of environment vars for specified container

        - name: name of the container
        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker command and output

    docker_shell(name, shell='sh', env_vars={}, show=False)
        Start shell on an existing container (will be started if stopped)

        - name: name of the container
        - shell: name of shell to execute
        - env_vars: a dict of environment variables and values to set
        - show: if True, show the docker command and output

    docker_cleanup_volumes(exception=False, show=False)
        Use this when creating a container fails with 'No space left on device'

        - exception: if True and docker has an error response, raise an exception
        - show: if True, show the docker command and output

        See: https://github.com/docker/machine/issues/1779
        See: https://github.com/chadoe/docker-cleanup-volumes
    ```

## Examples

```
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
```
