__all__ = [
    'docker_ok', 'docker_stop', 'docker_start_or_run', 'docker_container_id',
    'docker_container_inspect', 'docker_container_config', 'docker_container_env_vars',
    'docker_logs', 'docker_exec', 'docker_exec_wait', 'docker_shell', 'docker_cleanup_volumes',
    'docker_redis_start', 'docker_redis_cli', 'docker_mongo_start',
    'docker_mongo_cli', 'docker_postgres_start', 'docker_postgres_cli', 'docker_postgres_wait',
    'docker_mysql_start', 'docker_mysql_cli', 'docker_mysql_wait',
    'docker_alpine_start', 'docker_ubuntu_start', 'docker_fedora_start'
]


import json
import os
import bg_helper as bh
import input_helper as ih
from time import sleep


def docker_ok(exception=False):
    """Return True if docker is available and the docker daemon is running

    - exception: if True and docker not available, raise an exception
    """
    output = bh.run_output('docker ps')
    if 'CONTAINER ID' not in output:
        if exception:
            raise Exception(output)
        else:
            return False
    return True


def docker_stop(name, kill=False, signal='KILL', rm=False, exception=False,
                show=False):
    """Return True if successfully stopped

    - name: name of the container
    - kill: if True, kill the container instead of stopping
    - signal: signal to send to the container if kill is True
    - rm: if True, remove the container after stop/kill
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    """
    if not docker_ok(exception=exception):
        return False
    if kill is False:
        cmd = 'docker stop {}'.format(name)
    else:
        cmd = 'docker kill --signal {} {}'.format(signal, name)
    output = bh.run_output(cmd, show=show)
    if show is True:
        print(output)
    if "Error response from daemon:" in output:
        return False

    if rm is True:
        cmd = 'docker rm {}'.format(name)
        output = bh.run_output(cmd, show=show)
        if show is True:
            print(output)
        if "Error response from daemon:" in output:
            return False
    return True


def docker_start_or_run(name, image='', command='', detach=True, rm=False,
                        interactive=False, ports='', volumes='', platform='',
                        env_vars={}, exception=False, show=False, force=False):
    """Start existing container or create/run container

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
    - platform: platform to set if server is multi-platform capable
    - env_vars: a dict of environment variables and values to set
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating
    """
    if not docker_ok(exception=exception):
        return False
    if force is True:
        if not image:
            message = 'The "image" arg is required since force is True'
            if exception:
                raise Exception(message)
            elif show is True:
                print(message)
            return False
        else:
            docker_stop(name, rm=True, show=show)
    else:
        output = bh.run_output('docker start {}'.format(name), show=show)
        if show is True:
            print(output)
        if "Error response from daemon:" not in output and "error during connect" not in output:
            return True
        else:
            if not image:
                message = 'Could not start "{}", so "image" arg is required'.format(name)
                if exception:
                    raise Exception(message)
                elif show is True:
                    print(message)
                return False

    cmd_parts = []
    cmd_parts.append('docker run --name {}'.format(name))
    if rm is True:
        cmd_parts.append(' --rm')
    if interactive is True:
        cmd_parts.append(' --tty --interactive')
        detach = False
    if detach is True:
        cmd_parts.append(' --detach')
    if ports:
        for port_mapping in ih.string_to_list(ports):
            cmd_parts.append(' --publish {}'.format(port_mapping))
    if volumes:
        for volume_mapping in ih.string_to_list(volumes):
            cmd_parts.append(' --volume {}'.format(volume_mapping))
    if platform:
        cmd_parts.append(' --platform {}'.format(platform))
    if env_vars:
        for key, value in env_vars.items():
            cmd_parts.append(' --env {}={}'.format(key, value))
    cmd_parts.append(' {}'.format(image))
    if command:
        cmd_parts.append(' {}'.format(command))

    cmd = ''.join(cmd_parts)
    if interactive is True:
        ret_code = bh.run(cmd, show=show)
        if ret_code == 0:
            return True
        else:
            return False
    else:
        output = bh.run_output(cmd, show=show)
        if show is True:
            print(output)
        if "Error response from daemon:" in output or "no matching manifest" in output:
            if exception:
                raise Exception(output)
            else:
                return False
        else:
            return True


def docker_container_id(name):
    """Return the container ID for running container name

    - name: name of the container
    """
    if not docker_ok():
        return ''
    cmd = "docker ps | grep '\\b{}\\b$'".format(name) + " | awk '{print $1}'"
    return bh.run_output(cmd)


def docker_container_inspect(name, exception=False, show=False):
    """Return detailed information on specified container as a list

    - name: name of the container
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker command and output
    """
    if not docker_ok(exception=exception):
        return []
    cmd = 'docker container inspect {}'.format(name)
    output = bh.run_output(cmd, show=show)
    if not output.startswith('[]\nError:'):
        return json.loads(output)
    else:
        if exception:
            raise Exception(output)
        elif show is True:
            print(output)
        return []


def docker_container_config(name, exception=False, show=False):
    """Return dict of config information for specified container (from inspect)

    - name: name of the container
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker command and output
    """
    result = docker_container_inspect(name, exception=exception, show=show)
    if result:
        return result[0]['Config']
    else:
        return {}


def docker_container_env_vars(name, exception=False, show=False):
    """Return dict of environment vars for specified container

    - name: name of the container
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker command and output
    """
    container_config = docker_container_config(name, exception=exception, show=show)
    env_vars = {}
    for item in container_config.get('Env', []):
        key, value = item.split('=', 1)
        env_vars[key] = value
    return env_vars


def docker_logs(name, num_lines=None, follow=False, details=False,
                since='', until='', timestamps=False, show=False):
    """Show logs on an existing container

    - name: name of the container
    - num_lines: number of lines to show from the end of the logs
    - follow: if True, follow log output
    - details: if True, show extra details provided to logs
    - since: show logs since timestamp (iso format or relative)
    - until: show logs before timestamp (iso format or relative)
    - timestamps: if True, show timestamps
    - show: if True, show the docker command and output
    """
    if not docker_ok():
        return False
    cmd_parts = []
    cmd_parts.append('docker logs {}'.format(name))
    if num_lines:
        cmd_parts.append(' --tail {}'.format(num_lines))
    if follow:
        cmd_parts.append(' --follow')
    if details:
        cmd_parts.append(' --details')
    if since:
        cmd_parts.append(' --since {}'.format(since))
    if until:
        cmd_parts.append(' --until {}'.format(until))
    if timestamps:
        cmd_parts.append(' --timestamps')
    cmd = ''.join(cmd_parts)

    if follow:
        try:
            return bh.run(cmd, show=show)
        except KeyboardInterrupt:
            return
    else:
        return bh.run_output(cmd, show=show)


def docker_exec(name, command='pwd', output=False, env_vars={}, show=False):
    """Run shell command on an existing container (will be started if stopped)

    - name: name of the container
    - command: command to execute
    - output: If True, return output or error from command
        - otherwise, return the exit status
    - env_vars: a dict of environment variables and values to set
    - show: if True, show the docker command and output
    """
    if not docker_ok():
        return False
    cmd_parts = []
    cmd_parts.append('docker exec')
    if env_vars:
        for key, value in env_vars.items():
            cmd_parts.append(' --env {}={}'.format(key, value))
    cmd_parts.append(' {} {}'.format(name, command))
    cmd = ''.join(cmd_parts)
    docker_start_or_run(name, show=show)
    if output is True:
        return bh.run_output(cmd, show=show)
    else:
        return bh.run(cmd, show=show)


def docker_exec_wait(name, command='pwd', sleeptime=2, env_vars={}, show=False):
    """Wait for a shell command to succeed in an existing container (will be started if stopped)

    - name: name of the container
    - command: command to execute
    - sleeptime: time to sleep between checks
    - env_vars: a dict of environment variables and values to set
    - show: if True, show the docker command and output
    """
    if show is False:
        command += ' &>/dev/null'
    while True:
        try:
            result = docker_exec(
                name,
                command=command,
                output=False,
                env_vars=env_vars,
                show=show
            )
            if result != 0:
                if show is True:
                    print('\n(Exit status was {}; sleeping for {} seconds)'.format(
                        result,
                        sleeptime
                    ))
                sleep(sleeptime)
            else:
                return
        except KeyboardInterrupt:
            return


def docker_shell(name, shell='sh', env_vars={}, show=False):
    """Start shell on an existing container (will be started if stopped)

    - name: name of the container
    - shell: name of shell to execute
    - env_vars: a dict of environment variables and values to set
    - show: if True, show the docker command and output
    """
    if not docker_ok():
        return False
    cmd_parts = []
    cmd_parts.append('docker exec --tty --interactive')
    if env_vars:
        for key, value in env_vars.items():
            cmd_parts.append(' --env {}={}'.format(key, value))
    cmd_parts.append(' {} {}'.format(name, shell))
    cmd = ''.join(cmd_parts)
    docker_start_or_run(name, show=show)
    return bh.run(cmd, show=show)


def docker_cleanup_volumes(exception=False, show=False):
    """Use this when creating a container fails with 'No space left on device'

    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker command and output

    See: https://github.com/docker/machine/issues/1779
    See: https://github.com/chadoe/docker-cleanup-volumes
    """
    return docker_start_or_run(
        'cleanup-volumes',
        image='martin/docker-cleanup-volumes',
        rm=True,
        volumes=(
            '/var/run/docker.sock:/var/run/docker.sock:ro, '
            '/var/lib/docker:/var/lib/docker'
        ),
        exception=exception,
        show=show
    )


def docker_redis_start(name, version='6-alpine', port=6300, data_dir=None, aof=True,
                       interactive=False, rm=False, exception=False, show=False, force=False):
    """Start or create redis container

    - name: name for the container
    - version: redis image version
    - port: port to map into the container
    - data_dir: directory that will map to container's /data
        - specify absolute path or subdirectory of current directory
    - aof: if True, use appendonly.aof file
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating

    See: https://hub.docker.com/_/redis for image versions ("supported tags")
    """
    if data_dir:
        if not data_dir.startswith(os.path.sep):
            data_dir = os.path.join(os.getcwd(), data_dir)
        volumes = '{}:/data'.format(data_dir)
    else:
        volumes = ''
    if aof:
        command = 'redis-server --appendonly yes'
    else:
        command = ''
    return docker_start_or_run(
        name,
        image='redis:{}'.format(version),
        command=command,
        ports='{}:6379'.format(port),
        volumes=volumes,
        interactive=interactive,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_redis_cli(name, show=False):
    """Start redis-cli on an existing container (will be started if stopped)

    - name: name for the container
    - show: if True, show the docker command and output
    """
    return docker_shell(name, shell='redis-cli', show=show)


def docker_mongo_start(name, version='4.4', port=27000, username='mongouser',
                       password='some.pass', data_dir=None, interactive=False, rm=False,
                       exception=False, show=False, force=False):
    """Start or create mongo container

    - name: name for the container
    - version: mongo image version
    - port: port to map into the container
    - username: username to set for root user on first run
    - password: password to set for root user on first run
    - data_dir: directory that will map to container's /data/db
        - specify absolute path or subdirectory of current directory
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating

    See: https://hub.docker.com/_/mongo for image versions ("supported tags")
    """
    env_vars = {
        'MONGO_INITDB_ROOT_USERNAME': username,
        'MONGO_INITDB_ROOT_PASSWORD': password,
    }
    if data_dir:
        if not data_dir.startswith(os.path.sep):
            data_dir = os.path.join(os.getcwd(), data_dir)
        volumes = '{}:/data/db'.format(data_dir)
    else:
        volumes = ''
    return docker_start_or_run(
        name,
        image='mongo:{}'.format(version),
        ports='{}:27017'.format(port),
        volumes=volumes,
        env_vars=env_vars,
        interactive=interactive,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_mongo_cli(name, show=False):
    """Start mongo on an existing container (will be started if stopped)

    - name: name for the container
    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('MONGO_INITDB_ROOT_USERNAME')
    password = env_vars.get('MONGO_INITDB_ROOT_PASSWORD')
    cmd = 'mongo --username {} --password {}'.format(username, password)
    return docker_shell(name, shell=cmd, show=show)


def docker_postgres_start(name, version='13-alpine', port=5400, username='postgresuser',
                          password='some.pass', db='postgresdb', data_dir=None,
                          interactive=False, rm=False, exception=False, show=False,
                          force=False, wait=False, sleeptime=2):
    """Start or create postgres container

    - name: name for the container
    - version: postgres image version
    - port: port to map into the container
    - username: username to set as superuser on first run
    - password: password to set for superuser on first run
    - db: name of default database
    - data_dir: directory that will map to container's /var/lib/postgresql/data
        - specify absolute path or subdirectory of current directory
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating
    - wait: if True, don't return until mysql is able to accept connections
    - sleeptime: if wait is True, sleep this number of seconds before checks

    See: https://hub.docker.com/_/postgres for image versions ("supported tags")
    """
    env_vars = {
        'POSTGRES_USER': username,
        'POSTGRES_PASSWORD': password,
        'POSTGRES_DB': db,
    }
    if data_dir:
        if not data_dir.startswith(os.path.sep):
            data_dir = os.path.join(os.getcwd(), data_dir)
        volumes = '{}:/var/lib/postgresql/data'.format(data_dir)
    else:
        volumes = ''

    run_result =  docker_start_or_run(
        name,
        image='postgres:{}'.format(version),
        ports='{}:5432'.format(port),
        volumes=volumes,
        env_vars=env_vars,
        interactive=interactive,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )

    if wait is True:
        docker_postgres_wait(name, sleeptime=sleeptime, show=show)
    return run_result


def docker_postgres_cli(name, show=False):
    """Start psql on an existing container (will be started if stopped)

    - name: name for the container
    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('POSTGRES_USER')
    password = env_vars.get('POSTGRES_PASSWORD')
    database = env_vars.get('POSTGRES_DB')
    cmd = 'psql -U {} -d {}'.format(username, database)
    pw_var = {'PGPASSWORD': password}
    return docker_shell(name, shell=cmd, env_vars=pw_var, show=show)


def docker_postgres_wait(name, sleeptime=2, show=False):
    """Wait for psql an existing container (will be started if stopped)

    - name: name of the container
    - sleeptime: time to sleep between checks
    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('POSTGRES_USER')
    password = env_vars.get('POSTGRES_PASSWORD')
    database = env_vars.get('POSTGRES_DB')
    cmd = 'psql -U {} -d {} -c "SELECT datname FROM pg_database"'.format(username, database)
    pw_var = {'PGPASSWORD': password}
    return docker_exec_wait(
        name,
        command=cmd,
        sleeptime=sleeptime,
        env_vars=pw_var,
        show=show
    )


def docker_mysql_start(name, version='8.0', port=3300, root_password='root.pass',
                       username='mysqluser', password='some.pass', db='mysqldb',
                       data_dir=None, interactive=False, rm=False, exception=False,
                       show=False, force=False, wait=False, sleeptime=2):
    """Start or create mysql container

    - name: name for the container
    - version: mysql image version (or mysql/mysql-server for Mac M1)
    - port: port to map into the container
    - root_password: password to set for the root superuser account
    - username: username to set as superuser on first run
    - password: password to set for superuser on first run
    - db: name of default database
    - data_dir: directory that will map to container's /var/lib/mysql
        - specify absolute path or subdirectory of current directory
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating
    - wait: if True, don't return until mysql is able to accept connections
    - sleeptime: if wait is True, sleep this number of seconds before checks

    See: https://hub.docker.com/_/mysql for image versions ("supported tags")
    """
    env_vars = {
        'MYSQL_USER': username,
        'MYSQL_ROOT_PASSWORD': root_password,
        'MYSQL_PASSWORD': password,
        'MYSQL_DATABASE': db,
    }
    if data_dir:
        if not data_dir.startswith(os.path.sep):
            data_dir = os.path.join(os.getcwd(), data_dir)
        volumes = '{}:/var/lib/mysql'.format(data_dir)
    else:
        volumes = ''

    image_name = 'mysql'
    platform = ''
    uname_a = bh.run_output('uname -a')
    if 'Darwin' in uname_a and 'arm64' in uname_a:
        image_name = 'mysql/mysql-server'
        platform = 'linux/amd64'

    run_result = docker_start_or_run(
        name,
        image='{}:{}'.format(image_name, version),
        ports='{}:3306'.format(port),
        volumes=volumes,
        platform=platform,
        env_vars=env_vars,
        interactive=interactive,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )

    if wait is True:
        docker_mysql_wait(name, sleeptime=sleeptime, show=show)
    return run_result


def docker_mysql_cli(name, show=False):
    """Start mysql on an existing container (will be started if stopped)

    - name: name of the container
    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('MYSQL_USER')
    password = env_vars.get('MYSQL_PASSWORD')
    database = env_vars.get('MYSQL_DATABASE')
    cmd = 'mysql -u {} -D {}'.format(username, database)
    pw_var = {'MYSQL_PWD': password}
    return docker_shell(name, shell=cmd, env_vars=pw_var, show=show)


def docker_mysql_wait(name, sleeptime=2, show=False):
    """Wait for mysql an existing container (will be started if stopped)

    - name: name of the container
    - sleeptime: time to sleep between checks
    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('MYSQL_USER')
    password = env_vars.get('MYSQL_PASSWORD')
    database = env_vars.get('MYSQL_DATABASE')
    cmd = 'mysql -u {} -D {} --execute "SHOW DATABASES"'.format(username, database)
    pw_var = {'MYSQL_PWD': password}
    return docker_exec_wait(
        name,
        command=cmd,
        sleeptime=sleeptime,
        env_vars=pw_var,
        show=show
    )


def docker_alpine_start(name, version='3.12', command='sleep 86400', detach=True,
                        interactive=False, rm=False, exception=False,
                        show=False, force=False):
    """Start or create alpine container

    - name: name for the container
    - version: alpine image version
    - command: command to run (default is sleep for a day)
    - detach: if True, run comtainer in the background
        - if interactive is True, detach will be set to False
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating

    See: https://hub.docker.com/_/alpine for image versions ("supported tags")
    """
    return docker_start_or_run(
        name,
        image='alpine:{}'.format(version),
        command=command,
        interactive=interactive,
        detach=detach,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_ubuntu_start(name, version='18.04', command='sleep 86400', detach=True,
                        interactive=False, rm=False, exception=False,
                        show=False, force=False):
    """Start or create ubuntu container

    - name: name for the container
    - version: ubuntu image version
    - command: command to run (default is sleep for a day)
    - detach: if True, run comtainer in the background
        - if interactive is True, detach will be set to False
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating

    See: https://hub.docker.com/_/ubuntu for image versions ("supported tags")
    """
    return docker_start_or_run(
        name,
        image='ubuntu:{}'.format(version),
        command=command,
        interactive=interactive,
        detach=detach,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_fedora_start(name, version='33', command='sleep 86400', detach=True,
                        interactive=False, rm=False, exception=False,
                        show=False, force=False):
    """Start or create fedora container

    - name: name for the container
    - version: fedora image version
    - command: command to run (default is sleep for a day)
    - detach: if True, run comtainer in the background
        - if interactive is True, detach will be set to False
    - interactive: if True, keep STDIN open and allocate pseudo-TTY
    - rm: if True, automatically delete the container when it exits
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating

    See: https://hub.docker.com/_/fedora for image versions ("supported tags")
    """
    return docker_start_or_run(
        name,
        image='fedora:{}'.format(version),
        command=command,
        interactive=interactive,
        detach=detach,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )
