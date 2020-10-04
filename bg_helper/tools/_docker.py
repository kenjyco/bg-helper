__all__ = [
    'docker_ok', 'docker_stop', 'docker_start_or_run', 'docker_container_id',
    'docker_container_inspect', 'docker_container_config', 'docker_container_env_vars',
    'docker_shell', 'docker_cleanup_volumes',
    'docker_redis_start', 'docker_redis_cli', 'docker_mongo_start',
    'docker_mongo_cli', 'docker_postgres_start', 'docker_postgres_cli',
    'docker_mysql_start', 'docker_mysql_cli'
]


import json
import os
import bg_helper as bh
import input_helper as ih


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
                        interactive=False, ports='', volumes='', env_vars={},
                        exception=False, show=False, force=False):
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
        if "Error response from daemon:" not in output:
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
        if "Error response from daemon:" in output:
            if exception:
                raise Exception(output)
            else:
                return False
        else:
            return True


def docker_container_id(name):
    """Return the container ID for running container name"""
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
                       rm=False, exception=False, show=False, force=False):
    """Start or create redis container

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
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_redis_cli(name, show=False):
    """Start redis-cli on an existing container (will be started if stopped)

    - show: if True, show the docker command and output
    """
    return docker_shell(name, shell='redis-cli', show=show)


def docker_mongo_start(name, version='4.4', port=27000, username='mongouser',
                       password='some.pass', data_dir=None, rm=False,
                       exception=False, show=False, force=False):
    """Start or create mongo container

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
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_mongo_cli(name, show=False):
    """Start mongo on an existing container (will be started if stopped)

    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('MONGO_INITDB_ROOT_USERNAME')
    password = env_vars.get('MONGO_INITDB_ROOT_PASSWORD')
    cmd = 'mongo --username {} --password {}'.format(username, password)
    return docker_shell(name, shell=cmd, show=show)


def docker_postgres_start(name, version='13-alpine', port=5400, username='postgresuser',
                          password='some.pass', db='postgresdb', data_dir=None,
                          rm=False, exception=False, show=False, force=False):
    """Start or create postgres container

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
    return docker_start_or_run(
        name,
        image='postgres:{}'.format(version),
        ports='{}:5432'.format(port),
        volumes=volumes,
        env_vars=env_vars,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_postgres_cli(name, show=False):
    """Start psql on an existing container (will be started if stopped)

    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('POSTGRES_USER')
    password = env_vars.get('POSTGRES_PASSWORD')
    database = env_vars.get('POSTGRES_DB')
    cmd = 'psql -U {} -d {}'.format(username, database)
    pw_var = {'PGPASSWORD': password}
    return docker_shell(name, shell=cmd, env_vars=pw_var, show=show)


def docker_mysql_start(name, version='8.0', port=3300, root_password='root.pass',
                       username='mysqluser', password='some.pass', db='mysqldb',
                       data_dir=None, rm=False, exception=False, show=False, force=False):
    """Start or create postgres container

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
    return docker_start_or_run(
        name,
        image='mysql:{}'.format(version),
        ports='{}:3306'.format(port),
        volumes=volumes,
        env_vars=env_vars,
        detach=True,
        rm=rm,
        exception=exception,
        show=show,
        force=force
    )


def docker_mysql_cli(name, show=False):
    """Start mysql on an existing container (will be started if stopped)

    - show: if True, show the docker command and output
    """
    env_vars = docker_container_env_vars(name)
    username = env_vars.get('MYSQL_USER')
    password = env_vars.get('MYSQL_PASSWORD')
    database = env_vars.get('MYSQL_DATABASE')
    cmd = 'mysql -u {} -D {}'.format(username, database)
    pw_var = {'MYSQL_PWD': password}
    return docker_shell(name, shell=cmd, env_vars=pw_var, show=show)
