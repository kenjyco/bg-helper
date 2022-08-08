__all__ = [
    'ctx_repo_path_root', 'git_repo_path_root', 'git_clone', 'git_fetch',
    'git_origin_url', 'git_do', 'git_current_branch', 'git_current_tracking_branch',
    'git_last_tag', 'git_tag_message', 'git_last_tag_message', 'git_tags',
    'git_first_commit_id', 'git_last_commit_id', 'git_commits_since_last_tag',
    'git_unpushed_commits', 'git_untracked_files', 'git_stashlist',
    'git_status', 'git_info_dict', 'git_info_string', 'git_branch_date',
    'git_remote_branches', 'git_local_branches',
    'git_remote_branches_merged_with', 'git_local_branches_merged_with'
]

import re
import bg_helper as bh
import fs_helper as fh
import input_helper as ih
from contextlib import contextmanager
from io import StringIO
from os import chdir, getcwd
from os.path import join


RX_CONFIG_URL = re.compile('^url\s*=\s*(\S+)$')
RX_NON_TAG = re.compile(r'.*-\d+-g[a-f0-9]+$')


@contextmanager
def ctx_repo_path_root(path, fetch=False, debug=False, timeout=None,
                       exception=True, show=False):
    """Context manager to cd to root of git repo for path

    - path: relative or absolute path to a file or directory
    - fetch: if True, call git_fetch func once inside the correct directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
    - show: Show the `cd` commands before executing
    """
    oldpwd = getcwd()
    did_cd = False
    try:
        if path:
            repo_path_root = git_repo_path_root(path=path, exception=exception)
            if repo_path_root != oldpwd:
                if show:
                    print('\n$ cd {}'.format(repr(repo_path_root)))
                chdir(repo_path_root)
                did_cd = True
        if fetch:
            git_fetch(debug=debug, timeout=timeout, exception=exception, show=show)
        yield
    finally:
        if did_cd:
            if show:
                print('\n$ cd {}'.format(repr(oldpwd)))
            chdir(oldpwd)


def git_repo_path_root(path='', exception=False):
    """Return git repo path root for path, or None

    - path: relative or absolute path to a file or directory
        - current working directory is used if none is specified
    - exception: if True, raise a ValueError if path is not in a repo
    """
    repo_path_root = fh.repopath(path)
    if exception and repo_path_root is None:
        raise ValueError('{} is not in a git repo'.format(path))
    return repo_path_root


def git_clone(url, path='', name='', recursive=False, debug=False, timeout=None,
              exception=True, show=False):
    """Clone a repo

    - url: URL for a git repo
    - path: path to clone git repo to, if not using current working directory
    - name: name to clone the repo as, if not using the existing name
    - recursive: if True, pass --recursive to `git clone`
    - debug: if True, insert breakpoint right before subprocess.call
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    path = path or getcwd()
    name = name or url.rsplit('/', 1)[-1].replace('.git', '')
    recursive = '--recursive ' if recursive else ''
    local_path = join(path, name)
    if show:
        common_kwargs['stderr_to_stdout'] = True
    else:
        common_kwargs['stderr_to_stdout'] = False
    cmd = 'git clone {}{} {}'.format(recursive, url, local_path)

    ret_code = bh.run(cmd, **common_kwargs)
    if ret_code == 0:
        return local_path


def git_fetch(path='', output=False, debug=False, timeout=None, exception=True,
              show=False):
    """Perform `git fetch --all --prune`

    - path: path to git repo, if not using current working directory
    - output: if True, return output of `git fetch --all --prune`
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git fetch --all --prune'
    with ctx_repo_path_root(path, fetch=False, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if show:
            print(output)

    if output:
        return output


def git_do(path='', fetch=False, cmd=None, output=False, debug=False,
           timeout=None, exception=True, show=False):
    """Run specified cmd and either return the output or the exit status

    Return a list of any local files that are not tracked in the git repo

    - path: path to git repo, if not using current working directory
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - cmd: string with shell command (required)
    - output: if True, capture output of cmd and return it; otherwise return exit status of cmd
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    assert cmd, 'The cmd argument is required'
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        if output:
            result = bh.run_output(cmd, **common_kwargs)
        else:
            result = bh.run(cmd, **common_kwargs)

    return result


def git_origin_url(path=''):
    """Return url to remote origin (from .git/config file)

    - path: path to git repo, if not using current working directory
    """
    result = ''
    local_path = git_repo_path_root(path=path)
    if not local_path:
        return result
    cmd = 'grep "remote \\"origin\\"" -A 2 {}/.git/config | grep url'.format(local_path)
    output = bh.run_output(cmd)
    match = RX_CONFIG_URL.match(output)
    if match:
        result = match.group(1)

    return result


def git_current_branch(path='', debug=False, timeout=None, exception=True,
                       show=False):
    """Return current branch name

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git rev-parse --abbrev-ref HEAD'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        output = 'HEAD' if 'fatal:' in output else output

    return output


def git_current_tracking_branch(path='', debug=False, timeout=None,
                                exception=True, show=False):
    """Return remote tracking branch for current branch

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git branch -r'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        branch = git_current_branch(**common_kwargs)
        results = bh.tools.grep_output(
            output,
            pattern='/{}$'.format(branch),
            extra_pipe='grep -v HEAD'
        )

    if results:
        return results[0]


def git_last_tag(path='', debug=False, timeout=None, exception=True, show=False):
    """Return the most recent tag made

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git describe --tags $(git rev-list --tags --max-count=1 2>/dev/null) 2>/dev/null'
    with ctx_repo_path_root(path, **common_kwargs):
        common_kwargs['exception'] = False
        output = bh.run_output(cmd, **common_kwargs)
        output = '' if 'fatal:' in output else output

    return output


def git_tag_message(path='', debug=False, tag='', timeout=None, exception=True,
                    show=False):
    """Return the message for specified tag

    - path: path to git repo, if not using current working directory
    - tag: name of a tag that was made
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    message = ''
    with ctx_repo_path_root(path, **common_kwargs):
        if not tag:
            tag = git_last_tag(**common_kwargs)
            if not tag:
                return message
        cmd = 'git tag -n99 {}'.format(tag)
        output = bh.run_output(cmd, **common_kwargs)
        message = output.replace(tag, '').strip()

    return message


def git_last_tag_message(path='', debug=False, timeout=None, exception=True,
                         show=False):
    """Return the message for the most recent tag made

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git describe --tags $(git rev-list --tags --max-count=1 2>/dev/null) 2>/dev/null'
    with ctx_repo_path_root(path, **common_kwargs):
        tag = git_last_tag(**common_kwargs)
        message = git_tag_message(tag)

    return message


def git_tags(path='', debug=False, timeout=None, exception=True, show=False):
    """Return a list of all tags with most recent first

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    tags = []
    cmd = 'git describe --tags $(git rev-list --tags) 2>/dev/null'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return tags
        for tag in re.split('\r?\n', output):
            if not RX_NON_TAG.match(tag):
                tags.append(tag)

    return tags


def git_first_commit_id(path='', debug=False, timeout=None, exception=True,
                        show=False):
    """Get the first commit id for the repo

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git rev-list --max-parents=0 HEAD'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        output = '' if 'fatal:' in output else output

    return output


def git_last_commit_id(path='', debug=False, timeout=None, exception=True,
                       show=False):
    """Get the last commit id for the repo

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git log --no-merges  --format="%h" -1'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        output = '' if 'fatal:' in output else output

    return output


def git_commits_since_last_tag(path='', until='', debug=False, timeout=None,
                               exception=True, show=False):
    """Return a list of commits made since last_tag

    - path: path to git repo, if not using current working directory
    - until: a recent commit id to stop at (instead of last commit)
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing

    If no tag has been made, returns a list of commits since the first commit
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    commits = []
    with ctx_repo_path_root(path, **common_kwargs):
        tag = git_last_tag(**common_kwargs)
        if not tag:
            tag = git_first_commit_id(**common_kwargs)
            if not tag:
                return commits
        if not until:
            until = git_last_commit_id(**common_kwargs)
        cmd = 'git log --find-renames --no-merges --oneline {}..{}'.format(tag, until)
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return commits
        commits = ih.splitlines(output)

    return commits


def git_unpushed_commits(path='', debug=False, timeout=None, exception=True,
                         show=False):
    """Return a list of any local commits that have not been pushed

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    commits = []
    cmd = 'git log --find-renames --no-merges --oneline @{u}.. 2>/dev/null'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return commits
        if output:
            commits = ih.splitlines(output)

    return commits


def git_untracked_files(path='', debug=False, timeout=None, exception=True,
                        show=False):
    """Return a list of any local files that are not tracked in the git repo

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    files = []
    cmd = 'git ls-files -o --exclude-standard'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return files
        files = ih.splitlines(output)

    return files


def git_stashlist(path='', debug=False, timeout=None, exception=True, show=False):
    """Return a list of any local stashes

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    stashes = []
    cmd = 'git stash list'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return stashes
        stashes = ih.splitlines(output)

    return stashes


def git_status(path='', debug=False, timeout=None, exception=True, show=False):
    """Return a list of any modified or untracked files

    - path: path to git repo, if not using current working directory
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    cmd = 'git status -s'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return results
        results = ih.splitlines_and_strip(output)

    return results


def git_info_dict(path='', fetch=False, debug=False, timeout=None,
                  exception=True, show=False):
    """Return a dict of info about the repo

    - path: path to git repo, if not using current working directory
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    data = {}
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        repo_path_root = git_repo_path_root(path=path, exception=exception)
        if not repo_path_root:
            return data
        data['path_root'] = repo_path_root
        data['url'] = git_origin_url()
        data['branch'] = git_current_branch(**common_kwargs)
        data['branch_date'] = git_branch_date(branch=data['branch'], **common_kwargs)
        data['branch_tracking'] = git_current_tracking_branch(**common_kwargs)
        data['branch_tracking_date'] = git_branch_date(branch=data['branch_tracking'], **common_kwargs)
        data['last_tag'] = git_last_tag(**common_kwargs)
        data['status'] = git_status(**common_kwargs)
        data['stashes'] = git_stashlist(**common_kwargs)
        data['unpushed'] = git_unpushed_commits(**common_kwargs)
        data['commits_since_last_tag'] = git_commits_since_last_tag(**common_kwargs)
    return data


def git_info_string(path='', fetch=False, debug=False, timeout=None,
                    exception=True, show=False):
    """Build up a string of info from git_info_dict and return it

    - path: path to git repo, if not using current working directory
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        info = git_info_dict(**common_kwargs)
    if not info:
        return ''
    s = StringIO()
    s.write('{} .::. {} .::. {}'.format(
        info['path_root'], info['url'], info['branch']
    ))
    if info['branch_tracking']:
        s.write('\n- tracking: {}'.format(info['branch_tracking']))
        s.write('\n    - updated: {}'.format(info['branch_tracking_date']))
        s.write('\n    - local: {}'.format(info['branch_date']))
    if info['last_tag']:
        s.write('\n- last tag: {}'.format(info['last_tag']))
    if info['status']:
        s.write('\n- status:')
        for filestat in info['status']:
            s.write('\n    - {}'.format(filestat))
    if info['stashes']:
        s.write('\n\n- stashes:')
        for stash in info['stashes']:
            s.write('\n    - {}'.format(stash))
    if info['unpushed']:
        s.write('\n\n- unpushed commits:')
        for commit in info['unpushed']:
            s.write('\n    - {}'.format(commit))
    if info['commits_since_last_tag']:
        s.write('\n\n- commits since last tag')
        num_commits = len(info['commits_since_last_tag'])
        if num_commits > 10:
            s.write(' ({} total, showing last 10):'.format(num_commits))
        else:
            s.write(':')
        for commit in info['commits_since_last_tag'][:10]:
            s.write('\n    - {}'.format(commit))
    return s.getvalue()


def git_branch_date(path='', branch='', fetch=False, debug=False, timeout=None,
                    exception=False, show=False):
    """Return datetime string (and relative age) of branch

    - path: path to git repo, if not using current working directory
    - branch: name of branch
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing

    Prefix branch name with 'origin/' to get date info of remote branch
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    cmd = 'git show --format="%ci %cr" {} | head -n 1'.format(branch)
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)

    return output


def _dates_for_branches(path='', branches=None, debug=False, timeout=None,
                        exception=False, show=False):
    """Return list of dicts, ordered by most recent commit

    - path: path to git repo, if not using current working directory
    - branches: list of branch names
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    with ctx_repo_path_root(path, fetch=False, **common_kwargs):
        for branch in branches:
            if not branch:
                continue
            time_data = git_branch_date(branch='origin/{}'.format(branch), **common_kwargs)
            if 'fatal:' in time_data:
                time_data = ''
            results.append({'branch': branch, 'time': time_data})
        ih.sort_by_keys(results, 'time', reverse=True)
        return results


def git_remote_branches(path='', fetch=False, grep='', include_times=False,
                        debug=False, timeout=None, exception=True, show=False):
    """Return list of remote branch names or list of dicts (via `git ls-remote --heads`)

    - path: path to git repo, if not using current working directory
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - grep: `grep -iE` pattern to filter branches by (case-insensitive)
        - specify multiple patterns with '(first|second|...)'
    - include_times: if True, include info from git_branch_date in results
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing

    Results are alphabetized if include_times is False, otherwise ordered by most
    recent commit
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    cmd = 'git ls-remote --heads | cut -f 2- | cut -c 12-'
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return results
        matches = bh.tools.grep_output(output, pattern=grep)
        branches = [
            branch
            for branch in matches
            if not branch.startswith('From ')
        ]

        if include_times:
            results = _dates_for_branches(branches=branches, **common_kwargs)
        else:
            results = branches

    return results


def git_local_branches(path='', fetch=False,  grep='', include_times=False,
                       debug=False, timeout=None, exception=True, show=False):
    """Return list of local branch names or list of dicts (via `git branch`)

    - path: path to git repo, if not using current working directory
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - grep: `grep -iE` pattern to filter branches by (case-insensitive)
        - specify multiple patterns with '(first|second|...)'
    - include_times: if True, include info from git_branch_date in results
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing

    Results are alphabetized if include_times is False, otherwise ordered by most
    recent commit
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    cmd = 'git branch | cut -c 3-'
    with ctx_repo_path_root(path, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return results
        branches = bh.tools.grep_output(output, pattern=grep)

        if include_times:
            results = _dates_for_branches(branches=branches, **common_kwargs)
        else:
            results = branches

    return results


def git_remote_branches_merged_with(path='', branch='develop', fetch=False,
                                    include_times=False, debug=False, timeout=None,
                                    exception=False, show=False):
    """Return a list of branches on origin that have been merged with branch

    - path: path to git repo, if not using current working directory
    - branch: remote branch name (without leading 'origin/')
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - include_times: if True, include info from git_branch_date in results
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    cmd = 'git branch -r --merged origin/{}'.format(branch)
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return results
        branches = bh.tools.grep_output(
            output,
            pattern='origin/{}'.format(branch),
            invert=True,
            extra_pipe='cut -c 10-'
       )

        if include_times:
            results = _dates_for_branches(branches=branches, **common_kwargs)
        else:
            results = branches

    return results


def git_local_branches_merged_with(path='', branch='develop', fetch=False,
                                   include_times=False, debug=False, timeout=None,
                                   exception=False, show=False):
    """Return a list of local branches that have been merged with branch

    - path: path to git repo, if not using current working directory
    - branch: local branch name
    - fetch: if True, call git_fetch func before calling the generated `git` command
    - include_times: if True, include info from git_branch_date in results
    - debug: if True, insert breakpoint right before subprocess.check_output
    - timeout: number of seconds to wait before stopping cmd
    - exception: if True, raise a ValueError if path is not in a repo
        - also raise Exception if git command has an error
    - show: if True, show the `git` command before executing
    """
    common_kwargs = dict(debug=debug, timeout=timeout, exception=exception, show=show)
    results = []
    cmd = 'git branch --merged {} | cut -c 3-'.format(branch)
    with ctx_repo_path_root(path, fetch=fetch, **common_kwargs):
        output = bh.run_output(cmd, **common_kwargs)
        if not output or 'fatal:' in output:
            return results
        branches = bh.tools.grep_output(
            output,
            pattern='^{}$'.format(branch),
            invert=True,
       )

        if include_times:
            results = _dates_for_branches(branches=branches, **common_kwargs)
        else:
            results = branches

    return results
