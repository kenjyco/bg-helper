__all__ = [
    'pip_freeze', 'pip_install_editable'
]

import os.path
import sys
import bg_helper as bh
import input_helper as ih


PIP = os.path.join(sys.prefix, 'bin', 'pip')
if not os.path.isfile(PIP):
    PIP = os.path.join(sys.prefix, 'Scripts', 'pip')
    if not os.path.isfile(PIP):
        __all__ = []

IN_A_VENV = True
if sys.prefix == sys.base_prefix:
    IN_A_VENV = False


def pip_freeze(venv_only=True, debug=False, timeout=None, exception=True, show=False):
    """
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if pip command has an error
    - show: if True, show the `pip` command before executing
    """
    if venv_only and not IN_A_VENV:
        if exception:
            raise Exception('Not in a venv')
        return
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    if show:
        common_kwargs['stderr_to_stdout'] = True
    else:
        common_kwargs['stderr_to_stdout'] = False
    cmd = "{} freeze".format(PIP)
    return bh.run(cmd, **common_kwargs)


def pip_install_editable(paths, venv_only=True, debug=False, timeout=None, exception=True, show=False):
    """Pip install the given paths in "editable mode"

    - paths: local paths to projects to install in "editable mode"
        - list of strings OR string separated by any of , ; |
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if pip command has an error
    - show: if True, show the `pip` command before executing
    """
    if venv_only and not IN_A_VENV:
        if exception:
            raise Exception('Not in a venv')
        return
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    if show:
        common_kwargs['stderr_to_stdout'] = True
    else:
        common_kwargs['stderr_to_stdout'] = False
    paths = ih.get_list_from_arg_strings(paths)
    parts = [
        '-e {}'.format(repr(path))
        for path in paths
    ]
    cmd = "{} install {}".format(PIP, ' '.join(parts))
    return bh.run(cmd, **common_kwargs)
