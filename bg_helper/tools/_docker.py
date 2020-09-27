__all__ = [
    'docker_ok', 'docker_stop', 'docker_start_or_run', 'docker_container_id',
    'docker_container_inspect', 'docker_container_config', 'docker_container_env_vars',
    'docker_shell', 'docker_cleanup_volumes',
]


import json
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
    cmd = "docker ps | grep '\\b{}\\b$'".format(name) + " | awk '{print $1}'"
    return bh.run_output(cmd)


def docker_container_inspect(name, exception=False, show=False):
    """Return detailed information on specified container as a list

    - name: name of the container
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker command and output
    """
    cmd = 'docker container inspect {}'.format(name)
    output = bh.run_output(cmd, show=show)
    if not output.startswith('[]\nError:'):
        return json.loads(output)
    else:
        if exception:
            raise Exception(output)
        elif show is True:
            print(output)


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
