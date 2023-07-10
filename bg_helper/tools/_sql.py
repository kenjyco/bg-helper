__all__ = [
    'sql_start_dev_containers_with_suffix',
    'sql_start_test_containers_with_suffix',
]

import bg_helper as bh
try:
    import sql_helper as sqh
except (ImportError, ModuleNotFoundError):
    # sql-helper not installed
    sqh = None
else:
    from ._docker import docker_ok
    if not docker_ok():
        # Can't use docker
        sqh = None

if sqh is None:
    __all__ = []


def sql_start_dev_containers_with_suffix(exception=True, show=True, wait=True):
    """

    """
    raise NotImplementedError


def sql_start_test_containers_with_suffix(exception=True, show=True, wait=True):
    """

    """
    raise NotImplementedError
