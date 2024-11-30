__all__ = [
    'IN_A_VENV', 'PATH_TO_PIP', 'PATH_TO_SITE_PACKAGES', 'installed_packages',
    'installed_packages_by_dir', 'installed_packages_non_site_packages',
    'pip_freeze', 'pip_install_editable', 'pip_extras', 'pip_version',
    'pip_package_versions_available'
]

import os.path
import site
import sys
import bg_helper as bh
import input_helper as ih
try:
    ModuleNotFoundError
except NameError:
    class ModuleNotFoundError(ImportError):
        pass
try:
    from importlib_metadata import distributions, metadata, PackageNotFoundError
    no_metadata_warning_message = ''
except (ImportError, ModuleNotFoundError):
    try:
        from importlib.metadata import distributions, metadata, PackageNotFoundError
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

PATH_TO_SITE_PACKAGES = [
    p
    for p in site.getsitepackages()
    if p.endswith('site-packages')
][0]


def installed_packages(name_only=False):
    """Return a dict or list of installed packages from importlib_metadata.distributions

    - name_only: if True, return a list of package names only

    The dict values are the versions of the packages
    """
    if name_only:
        results = [dist.metadata['Name'] for dist in distributions()]
    else:
        results = {
            dist.metadata['Name']: dist.version
            for dist in distributions()
        }
    return results


def installed_packages_by_dir():
    """Return a dict of installed packages from importlib_metadata.distributions

    The 'standard' key will have a dict of standard packages and their versions.
    The 'other' key will have a dict of packages that are installed outside of
    PATH_TO_SITE_PACKAGES (editable installs)
    """
    results = {'standard': {}, 'other': {}}
    for dist in distributions():
        name = dist.metadata['Name']
        dist_path = os.path.dirname(dist._path)
        if dist_path == PATH_TO_SITE_PACKAGES:
            results['standard'][name] = dist.version
        else:
            results['other'][name] = dist_path

    return results


def installed_packages_non_site_packages():
    """Return a dict of installed packages from importlib_metadata.distributions

    Only include the packages that are not in PATH_TO_SITE_PACKAGES
    """
    results = {}
    for dist in distributions():
        name = dist.metadata['Name']
        dist_path = os.path.dirname(dist._path)
        if dist_path == PATH_TO_SITE_PACKAGES:
            continue
        results[name] = dist_path

    return results


def pip_freeze(pip_path='', venv_only=True, debug=False, timeout=None,
               exception=True, show=False):
    """
    - pip_path: absolute path to pip in a virtual environment
        - use derived PATH_TO_PIP if not specified
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if pip command has an error
    - show: if True, show the `pip` command before executing
    """
    if pip_path:
        venv_only = False
    elif PATH_TO_PIP:
        pip_path = PATH_TO_PIP
    else:
        if exception:
            raise Exception('No pip_path specified and derived PATH_TO_PIP is empty')
        return
    if venv_only and not IN_A_VENV:
        if exception:
            raise Exception('Not in a venv')
        return
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    if show:
        common_kwargs['stderr_to_stdout'] = True
    else:
        common_kwargs['stderr_to_stdout'] = False
    cmd = "{} freeze".format(pip_path)
    return bh.run(cmd, **common_kwargs)


def pip_install_editable(paths, pip_path='', venv_only=True, debug=False,
                         timeout=None, exception=True, show=False):
    """Pip install the given paths in "editable mode"

    - paths: local paths to projects to install in "editable mode"
        - list of strings OR string separated by any of , ; |
    - pip_path: absolute path to pip in a virtual environment
        - use derived PATH_TO_PIP if not specified
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if pip command has an error
    - show: if True, show the `pip` command before executing
    """
    if pip_path:
        venv_only = False
    elif PATH_TO_PIP:
        pip_path = PATH_TO_PIP
    else:
        message = 'No pip_path specified and derived PATH_TO_PIP is empty'
        if exception:
            raise Exception(message)
        print(message)
        return
    if venv_only and not IN_A_VENV:
        message = 'Not in a venv'
        if exception:
            raise Exception(message)
        print(message)
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
    cmd = "{} install {}".format(pip_path, ' '.join(parts))
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


def pip_version(pip_path='', venv_only=True, debug=False, exception=True):
    """Return a tuple for the pip version (major int, minor int, patch string)

    - pip_path: absolute path to pip in a virtual environment
        - use derived PATH_TO_PIP if not specified
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - exception: if True, raise Exception if pip command has an error
    """
    if pip_path:
        venv_only = False
    elif PATH_TO_PIP:
        pip_path = PATH_TO_PIP
    else:
        message = 'No pip_path specified and derived PATH_TO_PIP is empty'
        if exception:
            raise Exception(message)
        print(message)
        return
    if venv_only and not IN_A_VENV:
        message = 'Not in a venv'
        if exception:
            raise Exception(message)
        print(message)
        return
    common_kwargs = dict(debug=debug, exception=exception)
    cmd = "{} --version".format(pip_path)
    output = bh.run_output(cmd, **common_kwargs)
    version_match = bh.tools.grep_output(output, regex='pip (\S+) from.*')
    result = ih.string_to_version_tuple(version_match[0])
    return result


def pip_package_versions_available(package_name, pip_path='', venv_only=True,
                                   debug=False, exception=True):
    """Return a list of versions available on pypi for the given package

    - package_name: name of the package on pypi.org
    - pip_path: absolute path to pip in a virtual environment
        - use derived PATH_TO_PIP if not specified
    - venv_only: if True, only run pip if it's in a venv
    - debug: if True, insert breakpoint right before subprocess.check_output
    - exception: if True, raise Exception if pip command has an error

    See: https://stackoverflow.com/a/26664162
    """
    if pip_path:
        venv_only = False
    elif PATH_TO_PIP:
        pip_path = PATH_TO_PIP
    else:
        message = 'No pip_path specified and derived PATH_TO_PIP is empty'
        if exception:
            raise Exception(message)
        print(message)
        return
    if venv_only and not IN_A_VENV:
        message = 'Not in a venv'
        if exception:
            raise Exception(message)
        print(message)
        return
    major, minor, _ = pip_version(pip_path=pip_path)

    results = []
    if (major == 21 and minor >= 2) or major > 22:
        # version >= 21.2
        cmd = "{} index versions {}".format(pip_path, package_name)
        output = bh.run_output(cmd, debug=debug, exception=False)
        versions_string = bh.tools.grep_output(output, regex='Available versions: (.*)')
        if versions_string:
            results = versions_string[0].split(', ')
        elif exception:
            raise Exception(output)
        else:
            print(output)
    elif ((major == 20 and minor >= 3) or (major == 21 and minor == 0)):
        # 21.1 > version >= 20.3
        cmd = "{} install --use-deprecated=legacy-resolver {}==".format(pip_path, package_name)
        output = bh.run_output(cmd, debug=debug, exception=False)
        versions_string = bh.tools.grep_output(output, regex='.*from versions: (.*)\)')
        if versions_string:
            results = sorted(versions_string[0].split(', '), reverse=True)
        elif exception:
            raise Exception(output)
        else:
            print(output)
    elif major >= 9:
        # version >= 9.0
        cmd = "{} install {}==".format(pip_path, package_name)
        output = bh.run_output(cmd, debug=debug, exception=False)
        if 'problem confirming the ssl certificate' in output:
            cmd = "{} install --trusted-host pypi.python.org {}==".format(pip_path, package_name)
            output = bh.run_output(cmd, debug=debug, exception=False)
        versions_string = bh.tools.grep_output(output, regex='.*from versions: (.*)\)')
        if versions_string:
            results = sorted(versions_string[0].split(', '), reverse=True)
        elif exception:
            raise Exception(output)
        else:
            print(output)

    return results
