__all__ = ['docker_ok']


import bg_helper as bh


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
