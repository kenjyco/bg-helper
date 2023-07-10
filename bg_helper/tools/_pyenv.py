__all__ = [
    'PATH_TO_PYENV', 'pyenv_install_python_version', 'pyenv_update',
    'pyenv_get_installable_versions', 'pyenv_get_versions'
]

import os.path
import re
import sys
import bg_helper as bh
import fs_helper as fh
import input_helper as ih
from glob import glob
from os import makedirs


_pyenv_repo_path = fh.abspath('~/.pyenv')
if not os.path.isdir(_pyenv_repo_path):
    __all__ = []

_rx_ignore_version_names = re.compile(r'.*-(dev|src|latest)$')
_rx_version_strings = re.compile(r'(?P<type_prefix>[a-z][^-]+-)?(?P<major_minor>\d+\.\d+).*')

PATH_TO_PYENV = os.path.join(_pyenv_repo_path, 'bin', 'pyenv')
if not os.path.isfile(PATH_TO_PYENV):
    PATH_TO_PYENV = ''


def pyenv_install_python_version(version):
    """Use pyenv to install a version of Python
    """
    cmd = '{} install {}'.format(PATH_TO_PYENV, version)
    ret_code = bh.run(cmd, stderr_to_stdout=True, show=True)
    if ret_code == 0:
        return True


def pyenv_update(show=True):
    """Update pyenv

    - show: if True,
    """
    if sys.platform == 'darwin':
        # Should probably check to see if brew is installed first
        ret_code = bh.run('brew upgrade pyenv', show=show)
        if ret_code == 0:
            return True
    else:
        return bh.tools.git_repo_update(_pyenv_repo_path, show=show)


def pyenv_get_installable_versions(only_py3=True, only_latest_per_group=True):
    """Return a list of Python versions that can be installed to ~/.pyenv/versions

    - only_py3: if True, only list standard Python 3.x versions
    - only_latest_per_group: if True, only include the latest version per group (non-dev)
    """
    cmd = '{} install --list'.format(PATH_TO_PYENV)
    output = bh.run_output(cmd)
    if only_py3:
        results = bh.tools.grep_output(output, regex='^  (3.*)')
    else:
        results = ih.splitlines_and_strip(output)

    if only_latest_per_group:
        last_full_version_string = ''
        last_major_minor = ''
        subset = []
        for version in results:
            if _rx_ignore_version_names.match(version):
                continue
            match = _rx_version_strings.match(version)
            if match:
                major_minor = match.groupdict()['major_minor']
                if major_minor != last_major_minor and last_full_version_string:
                    subset.append(last_full_version_string)
                last_full_version_string = version
                last_major_minor = major_minor

        if subset:
            last_major_minor = _rx_version_strings.match(subset[-1]).groupdict()['major_minor']
            if major_minor != last_major_minor:
                subset.append(last_full_version_string)
            results = subset

    return results


def pyenv_get_versions():
    """Return a list of Python versions locally installed to ~/.pyenv/versions
    """
    cmd = 'ls -1 {}'.format(os.path.join(_pyenv_repo_path, 'versions'))
    return ih.splitlines(bh.run_output(cmd))
