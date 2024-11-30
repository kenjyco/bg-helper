__all__ = [
    'PATH_TO_PYENV', 'pyenv_install_python_version', 'pyenv_update',
    'pyenv_get_installable_versions', 'pyenv_select_python_versions_to_install',
    'pyenv_get_versions', 'pyenv_path_to_python_version', 'pyenv_pip_versions',
    'pyenv_pip_package_versions_available',
    'pyenv_create_venvs_for_py_versions_and_dep_versions'
]

import itertools
import os.path
import re
import sys
import bg_helper as bh
import fs_helper as fh
import input_helper as ih
from glob import glob
from os import listdir, makedirs
from shutil import rmtree


_pyenv_repo_path = fh.abspath('~/.pyenv')
if not os.path.isdir(_pyenv_repo_path):
    __all__ = []

_rx_version_strings = re.compile(r'(?P<type_prefix>[a-z][^-]+-)?(?P<major_minor>\d+\.\d+).*')
_rx_non_release = re.compile(r'.*(\d+.*[a-z]+|-dev$|-latest$)')

PATH_TO_PYENV = os.path.join(_pyenv_repo_path, 'bin', 'pyenv')
if not os.path.isfile(PATH_TO_PYENV):
    PATH_TO_PYENV = ''


def pyenv_install_python_version(*versions):
    """Use pyenv to install versions of Python

    - versions: a list of versions to install
        - can also be a list of versions contained in a single string, separated
          by one of , ; |
    """
    results = []
    versions = ih.get_list_from_arg_strings(versions)

    for version in versions:
        cmd = '{} install {}'.format(PATH_TO_PYENV, version)
        ret_code = bh.run(cmd, stderr_to_stdout=True, show=True)
        if ret_code == 0:
            results.append((version, True))
        else:
            results.append((version, False))
    return results


def pyenv_update(show=True):
    """Update pyenv

    - show: if True, show the command before executing
    """
    if sys.platform == 'darwin':
        # Should probably check to see if brew is installed first
        ret_code = bh.run('brew upgrade pyenv', show=show)
        if ret_code == 0:
            return True
    else:
        return bh.tools.git_repo_update(_pyenv_repo_path, show=show)


def pyenv_get_installable_versions(only_py3=True, only_latest_per_group=True,
                                   only_released=True, only_non_released=False):
    """Return a list of Python versions that can be installed to ~/.pyenv/versions

    - only_py3: if True, only list standard Python 3.x versions
    - only_latest_per_group: if True, only include the latest version per group
    - only_released: if True, only include released versions, not alpha/beta/rc/dev/src
    - only_non_released: if True, only include non-released versions, like alpha/beta/rc/dev/src
    """
    if only_non_released:
        only_released = False
    cmd = '{} install --list'.format(PATH_TO_PYENV)
    output = bh.run_output(cmd)
    if only_py3:
        results = bh.tools.grep_output(output, regex=r'^  (3.*)')
    else:
        results = ih.splitlines_and_strip(output)

    if only_released:
        results = [
            version
            for version in results
            if not _rx_non_release.match(version)
        ]
    elif only_non_released:
        results = [
            version
            for version in results
            if _rx_non_release.match(version)
        ]

    if only_latest_per_group:
        last_full_version_string = ''
        last_major_minor = ''
        subset = []
        for version in results:
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


def pyenv_select_python_versions_to_install(only_py3=True, only_latest_per_group=True,
                                            only_released=True, only_non_released=False):
    """Select versions of Python to install with pyenv

    - only_py3: if True, only select from standard Python 3.x versions
    - only_latest_per_group: if True, only include the latest version per group
    - only_released: if True, only include released versions, not alpha/beta/rc/dev/src
    - only_non_released: if True, only include non-released versions, like alpha/beta/rc/dev/src

    See: pyenv_get_installable_versions
    """
    versions = pyenv_get_installable_versions(
        only_py3=only_py3,
        only_latest_per_group=only_latest_per_group,
        only_released=only_released,
        only_non_released=only_non_released
    )

    prompt = 'Select versions of Python to install with pyenv'
    selected = ih.make_selections(versions, prompt=prompt)
    if selected:
       return  pyenv_install_python_version(selected)


def pyenv_get_versions():
    """Return a list of Python versions locally installed to ~/.pyenv/versions
    """
    return listdir(os.path.join(_pyenv_repo_path, 'versions'))


def pyenv_path_to_python_version(version):
    """Return path to the installed Python binary for the given version or None"""
    py_path = os.path.join(_pyenv_repo_path, 'versions', version, 'bin', 'python')
    if os.path.isfile(py_path):
        return py_path


def pyenv_pip_versions(py_versions=''):
    """Return a dict of default pip versions for each given Python version

    - py_versions: string containing locally installed Python versions
      separated by any of , ; |
        - if none specified, use all local versions returned from
          pyenv_get_versions()

    Calls pip_version
    """
    py_versions = ih.get_list_from_arg_strings(py_versions)
    if not py_versions:
        py_versions = pyenv_get_versions()

    results = {}
    for py_version in sorted(py_versions):
        pip_path = os.path.join(_pyenv_repo_path, 'versions', py_version, 'bin', 'pip')
        if not os.path.isfile(pip_path):
            continue
        results[py_version] = bh.tools.pip_version(pip_path=pip_path)
    return results


def pyenv_pip_package_versions_available(package_name, py_versions='', show=False):
    """Return a dict of package versions available on pypi for the given package

    - package_name: name of the package on pypi.org
    - py_versions: string containing locally installed Python versions
      separated by any of , ; |
        - if none specified, use all local versions returned from
          pyenv_get_versions()
    - show: if True, display the results

    Calls pip_package_versions_available
    """
    py_versions = ih.get_list_from_arg_strings(py_versions)
    if not py_versions:
        py_versions = pyenv_get_versions()

    results = {}
    for py_version in sorted(py_versions):
        pip_path = os.path.join(_pyenv_repo_path, 'versions', py_version, 'bin', 'pip')
        if not os.path.isfile(pip_path):
            continue
        package_versions = bh.tools.pip_package_versions_available(
            package_name,
            pip_path=pip_path
        )
        results[py_version] = package_versions
        if show:
            print('\n{} -> {}'.format(py_version, package_versions))
    return results


def pyenv_create_venvs_for_py_versions_and_dep_versions(base_dir, py_versions='',
                                                        pip_version='',
                                                        pip_latest=False,
                                                        wheel_version='',
                                                        wheel_latest=False,
                                                        clean=False,
                                                        die=False,
                                                        local_package_paths='',
                                                        extra_packages='',
                                                        dep_versions_dict=None):
    """Create a combination of venvs for the given py_versions and dep_versions

    - base_dir: path to directory where the venvs will be created
    - py_versions: string containing Python versions to make venvs for separated
      by any of , ; |
        - if none specified, use all local versions returned from
          pyenv_get_versions()
    - pip_version: specific version of pip to install first
    - pip_latest: if True, install latest version of pip
        - ignored if pip_version specified
    - wheel_version: specific version of wheel to install first
    - wheel_latest: if True, install latest version of wheel
        - ignored if wheel_version specified
    - clean: if True, delete any existing venv that would be created if it exists
    - die: if True, return if any part of venv creation or pip install fails
    - local_package_paths: local paths to projects to install in "editable mode"
        - may be a list or string of paths separated by one of , ; |
    - extra_packages: string of extra packages to be installed in each venv
        - may be a list or string of package names separated by one of , ; |
        - package names may include version (i.e. package_name==version)
    - dep_versions_dict: dict where keys are package names and values are specific versions
        - versions may be a list or string of versions separated by one of , ; |
    """
    base_dir = fh.abspath(base_dir)
    makedirs(base_dir, exist_ok=True)
    py_versions = ih.get_list_from_arg_strings(py_versions)
    local_package_paths = [
        fh.abspath(local_path)
        for local_path in ih.get_list_from_arg_strings(local_package_paths)
    ]
    extra_packages = ih.get_list_from_arg_strings(extra_packages)
    if dep_versions_dict:
        dep_names = sorted([name for name in dep_versions_dict])
        dep_versions_lists = [
            ih.string_to_list(dep_versions_dict[dep_name])
            for dep_name in dep_names
        ]
        dep_versions_combinations = list(itertools.product(*dep_versions_lists))
    if not py_versions:
        py_versions = pyenv_get_versions()

    initial_pip_cmd = ''
    if pip_version:
        initial_pip_cmd = 'pip=={}'.format(pip_version)
    elif pip_latest:
        initial_pip_cmd = '--upgrade pip'
    if wheel_version:
        initial_pip_cmd += ' wheel=={}'.format(wheel_version)
    elif wheel_latest:
        initial_pip_cmd += ' wheel'

    main_pip_cmd_parts = []
    if local_package_paths:
        main_pip_cmd_parts = [
            '-e {}'.format(repr(path))
            for path in local_package_paths
        ]
    if extra_packages:
        main_pip_cmd_parts += [repr(pkg) for pkg in extra_packages]

    venvs_and_commands = []
    for py_version in py_versions:
        py_path = pyenv_path_to_python_version(py_version)
        if not py_path:
            pyenv_install_python_version(py_version)
            py_path = pyenv_path_to_python_version(py_version)
            if not py_path:
                continue

        py35_part = ''
        if py_version.startswith('3.5.'):
            py35_part = '--trusted-host pypi.python.org '

        if not dep_versions_dict:
            venv_name = 'venv_py{}'.format(py_version)
            venv_path = os.path.join(base_dir, venv_name)
            pip_path = os.path.join(venv_path, 'bin', 'pip')
            cmd_pip_setup = ''
            if initial_pip_cmd:
                cmd_pip_setup = '{} install {}{}'.format(pip_path, py35_part, initial_pip_cmd)
            if main_pip_cmd_parts:
                cmd_pip_install = '{} install {}{}'.format(pip_path, py35_part, ' '.join(main_pip_cmd_parts))

            venvs_and_commands.append({
                'py_path': py_path,
                'venv_path': venv_path,
                'pip_path': pip_path,
                'cmd_venv_create': '{} -m venv {}'.format(py_path, venv_path),
                'cmd_pip_setup': cmd_pip_setup,
                'cmd_pip_install': cmd_pip_install
            })
        else:
            for dep_combination in dep_versions_combinations:
                dep_dict = dict(zip(dep_names, dep_combination))
                dep_parts = ['{}{}'.format(name, version) for name, version in sorted(dep_dict.items())]
                venv_name = 'venv_py{}_'.format(py_version) + '_'.join(dep_parts)
                venv_path = os.path.join(base_dir, venv_name.strip('_'))
                pip_path = os.path.join(venv_path, 'bin', 'pip')

                cmd_pip_setup = ''
                if initial_pip_cmd:
                    cmd_pip_setup = '{} install {}{}'.format(pip_path, py35_part, initial_pip_cmd)

                cmd_parts = main_pip_cmd_parts + [
                    '{}=={}'.format(name, version)
                    for name, version in dep_dict.items()
                ]
                cmd_pip_install = '{} install {}{}'.format(pip_path, py35_part, ' '.join(cmd_parts))

                venvs_and_commands.append({
                    'py_path': py_path,
                    'venv_path': venv_path,
                    'pip_path': pip_path,
                    'cmd_venv_create': '{} -m venv {}'.format(py_path, venv_path),
                    'cmd_pip_setup': cmd_pip_setup,
                    'cmd_pip_install': cmd_pip_install
                })

    for cmd_set in venvs_and_commands:
        if clean and os.path.isdir(cmd_set['venv_path']):
            rmtree(cmd_set['venv_path'])

        if not os.path.isdir(cmd_set['venv_path']):
            ret_code = bh.run(cmd_set['cmd_venv_create'], stderr_to_stdout=True, show=True)
            if ret_code != 0:
                rmtree(cmd_set['venv_path'])
                if die:
                    return
            if cmd_set['cmd_pip_setup']:
                ret_code = bh.run(cmd_set['cmd_pip_setup'], stderr_to_stdout=True, show=True)
                if ret_code != 0:
                    rmtree(cmd_set['venv_path'])
                    if die:
                        return
            ret_code = bh.run(cmd_set['cmd_pip_install'], stderr_to_stdout=True, show=True)
            if ret_code != 0:
                rmtree(cmd_set['venv_path'])
                if die:
                    return
