__all__ = [
    'IN_A_VENV', 'PATH_TO_PIP', 'pip_freeze', 'pip_install_editable', 'pip_extras'
]

import os.path
import sys
import bg_helper as bh
import input_helper as ih
try:
    from importlib_metadata import metadata, PackageNotFoundError
    no_metadata_warning_message = ''
except (ImportError, ModuleNotFoundError):
    try:
        from importlib.metadata import metadata, PackageNotFoundError
        no_metadata_warning_message = ''
    except (ImportError, ModuleNotFoundError):
        no_metadata_warning_message = 'Could not find importlib_metadata. Try to install with: pip3 install importlib_metadata'
        metadata = None


PATH_TO_PIP = os.path.join(sys.prefix, 'bin', 'pip')
if not os.path.isfile(PATH_TO_PIP):
    PATH_TO_PIP = os.path.join(sys.prefix, 'Scripts', 'pip')
    if not os.path.isfile(PATH_TO_PIP):
        PATH_TO_PIP = ''

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


def pip_extras(package_name, venv_only=True, exception=True):
    """Return the extras_requires keys for specified package

    - package_name: Name of the package to get extras_requires keys
    - venv_only: if True, only run pip if it's in a venv
    - exception: if True, raise Exception if pip command has an error
    """
    if venv_only and not IN_A_VENV:
        message = 'Not in a venv'
        if exception:
            raise Exception('Not in a venv')
        print('Not in a venv')
        return

    if metadata is None:
        if exception:
            raise Exception(no_metadata_warning_message)
        else:
            print(no_metadata_warning_message)
        return

    try:
        results = metadata(package_name).get_all('Provides-Extra')
    except PackageNotFoundError:
        pass
    else:
        return results
