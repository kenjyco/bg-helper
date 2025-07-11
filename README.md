`bg-helper` is a Python library that provides production-ready shell command orchestration, Docker service management, git repository automation, and more. It offers three core execution primitives (`run`, `run_output`, `run_or_die`) with universal timeout protection and error handling, plus specialized tools for managing Docker containers (PostgreSQL, MySQL, Redis, MongoDB), git operations with automatic context management, and Python environment automation via pyenv. Rather than hiding complexity behind abstractions, `bg-helper` provides powerful primitives for shell command orchestration, background task management, and DevOps workflow automation. You can always pass `show=True` to see the actual commands being executed, learn the underlying tools, and build transferable skills while providing comprehensive error capture and background task management.

**Who benefits from this?**
- **DevOps engineers** who need reliable automation for git repositories, Docker containers, and development environments
- **Systems administrators** who want Python's power while preserving shell command fidelity
- **Infrastructure teams** building automation that must be debuggable, maintainable, and transparent
- **Library developers** who need robust local integration testing with multiple database services and Python versions
- **Anyone** who has been burned by "magic" tools and wants infrastructure code that reveals rather than conceals its operations

`bg-helper` fits naturally into existing toolchains by wrapping and enhancing familiar tools (git, docker, ssh) rather than replacing them. It's designed for REPL-driven exploration that gradually evolves into production automation.

**Particularly useful for integration testing:** The Docker service functions enable easy local testing across multiple database types (PostgreSQL, MySQL, Redis, MongoDB), while the pyenv functions support testing across Python versions. The `pyenv_create_venvs_for_py_versions_and_dep_versions` function is especially powerful for creating test matrices across Python versions and dependency combinations, as demonstrated in libraries like sql-helper.

## Install

```
pip install bg-helper
```

## QuickStart

```python
import bg_helper as bh

# Safe command execution with timeout protection and error capture
result = bh.run_output('ls -la', show=True)  # Shows actual command executed
print(result)

# Comprehensive error handling for any function
error_info = bh.call_func(lambda: 1/0)
if error_info['status'] == 'error':
    print(f"Function failed: {error_info['error_type']}")
    print(f"Full traceback: {error_info['traceback_string']}")

# Git operations with automatic repository context management
branch = bh.tools.git_current_branch(show=True)  # Learn the actual git commands
print(f"Current branch: {branch}")

# Docker service management with intelligent fallback logic
success = bh.tools.docker_postgres_start(
    name='dev-db',
    port=5432,
    show=True  # See exactly what Docker commands are executed
)

# Background task execution with comprehensive error logging
task = bh.SimpleBackgroundTask('long-running-command --with-args')
```

**What you gain:** Reliable shell command orchestration with production-grade error handling, automatic resource cleanup, timeout protection, and complete operational transparency. Every operation can show you the exact commands being executed, making debugging and learning seamless.

## API Overview

### Core Execution Primitives

These three functions form the foundation for all shell command operations, providing graduated levels of strictness:

- **`run(cmd, stderr_to_stdout=False, debug=False, timeout=None, exception=False, show=False)`** - Execute a shell command and return the exit status
  - `cmd`: Shell command string to execute
  - `stderr_to_stdout`: Redirect stderr to stdout if True
  - `debug`: Insert pdb breakpoint before execution if True
  - `timeout`: Seconds to wait before stopping command (prevents hanging)
  - `exception`: Raise exception on non-zero exit status if True
  - `show`: Display the actual command before execution if True
  - Returns: Integer exit status
  - Internal calls: None

- **`run_output(cmd, strip=True, debug=False, timeout=None, exception=False, show=False)`** - Execute a shell command and return its output
  - `cmd`: Shell command string to execute
  - `strip`: Remove leading/trailing whitespace from output if True
  - `debug`: Insert pdb breakpoint before execution if True
  - `timeout`: Seconds to wait before stopping command
  - `exception`: Raise exception on command failure if True
  - `show`: Display the actual command before execution if True
  - Returns: Command output as string
  - Internal calls: None

- **`run_or_die(cmd, stderr_to_stdout=False, debug=False, timeout=None, exception=True, show=False)`** - Execute a shell command with strict error handling—fail fast on any error
  - `cmd`: Shell command string to execute
  - `stderr_to_stdout`: Redirect stderr to stdout if True
  - `debug`: Insert pdb breakpoint before execution if True
  - `timeout`: Seconds to wait before stopping command
  - `exception`: If True (default), raise exception on failure; if False, exit process
  - `show`: Display the actual command before execution if True
  - Returns: Integer exit status (only on success)
  - Internal calls: None

### Error Handling and Background Tasks

- **`call_func(func, *args, **kwargs)`** - Execute any Python function with comprehensive error capture and forensic information
  - `func`: Python function to execute
  - `*args`: Arguments to pass to function
  - `**kwargs`: Keyword arguments (special kwargs: `logger`, `verbose`)
  - Returns: Dictionary with keys: `func_name`, `args`, `kwargs`, `status` (always present); `value` (on success); `error_type`, `error_value`, `traceback_string`, `fqdn`, `time_epoch`, `time_string`, `func_doc`, `func_module` (on error)
  - Internal calls: None

- **`SimpleBackgroundTask(func, *args, **kwargs)`** - Execute a function or shell command in a background daemon thread with automatic error logging
  - `func`: Python callable or shell command string
  - `*args`: Arguments for callable (ignored for shell commands)
  - `**kwargs`: Keyword arguments for callable
  - Returns: Background task object (daemon threads won't prevent process exit)
  - Internal calls: `call_func()`

### Git Operations (`bh.tools.*`)

Git functions provide repository automation with automatic context management and state isolation.

- **`ctx_repo_path_root(path, fetch=False, debug=False, timeout=None, exception=True, show=False)`** - Context manager that changes to the root directory of a git repository
  - `path`: Path to file or directory in git repository
  - `fetch`: Execute `git fetch` after changing directory if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if path not in repo or fetch fails if True
  - `show`: Display directory change commands if True
  - Returns: Context manager
  - Internal calls: `git_repo_path_root()`, `git_fetch()`

- **`git_repo_path_root(path='', exception=False)`** - Return git repo path root for path, or None
  - `path`: Relative or absolute path to file or directory (current working directory used if none specified)
  - `exception`: Raise ValueError if path is not in a repo if True
  - Returns: String path to repo root or empty string
  - Internal calls: `fh.repopath()`

- **`git_repo_update(path='', debug=False, timeout=None, exception=True, show=False)`** - Update a repo and return True if it was successful
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Boolean success status
  - Internal calls: `ctx_repo_path_root()`, `git_current_tracking_branch()`, `git_current_branch()`, `git_origin_url()`, `git_fetch()`, `bh.run_output()`, `bh.run()`

- **`git_clone(url, path='', name='', recursive=False, debug=False, timeout=None, exception=True, show=False)`** - Clone a repo
  - `url`: URL for a git repo
  - `path`: Path to clone git repo to, if not using current working directory
  - `name`: Name to clone the repo as, if not using the existing name
  - `recursive`: Pass --recursive to `git clone` if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Local path to cloned repo or None
  - Internal calls: `bh.run()`

- **`git_fetch(path='', output=False, debug=False, timeout=None, exception=True, show=False)`** - Perform `git fetch --all --prune`
  - `path`: Path to git repo, if not using current working directory
  - `output`: Return output of `git fetch --all --prune` if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Command output if output=True, otherwise None
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_do(path='', fetch=False, cmd=None, output=False, debug=False, timeout=None, exception=True, show=False)`** - Run specified cmd and either return the output or the exit status
  - `path`: Path to git repo, if not using current working directory
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `cmd`: String with shell command (required)
  - `output`: Capture output of cmd and return it if True; otherwise return exit status of cmd
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Command output or exit status depending on output parameter
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `bh.run()`

- **`git_origin_url(path='')`** - Return url to remote origin (from .git/config file)
  - `path`: Path to git repo, if not using current working directory
  - Returns: String URL or empty string
  - Internal calls: `git_repo_path_root()`, `bh.run_output()`

- **`git_current_branch(path='', debug=False, timeout=None, exception=False, show=False)`** - Return current branch name
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String branch name
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_current_tracking_branch(path='', debug=False, timeout=None, exception=False, show=False)`** - Return remote tracking branch for current branch
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String tracking branch name or empty string
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `git_current_branch()`, `bh.tools.grep_output()`

- **`git_last_tag(path='', debug=False, timeout=None, exception=False, show=False)`** - Return the most recent tag made
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String tag name or empty string
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_tag_message(path='', debug=False, tag='', timeout=None, exception=False, show=False)`** - Return the message for specified tag
  - `path`: Path to git repo, if not using current working directory
  - `tag`: Name of a tag that was made
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String tag message
  - Internal calls: `ctx_repo_path_root()`, `git_last_tag()`, `bh.run_output()`

- **`git_last_tag_message(path='', debug=False, timeout=None, exception=False, show=False)`** - Return the message for the most recent tag made
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String tag message
  - Internal calls: `ctx_repo_path_root()`, `git_last_tag()`, `git_tag_message()`

- **`git_tags(path='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of all tags with most recent first
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of tag names
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_first_commit_id(path='', debug=False, timeout=None, exception=False, show=False)`** - Get the first commit id for the repo
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String commit ID or empty string
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_last_commit_id(path='', debug=False, timeout=None, exception=False, show=False)`** - Get the last commit id for the repo
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String commit ID or empty string
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_commits_since_last_tag(path='', until='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of commits made since last_tag
  - `path`: Path to git repo, if not using current working directory
  - `until`: A recent commit id to stop at (instead of last commit)
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of commit strings (if no tag, returns commits since first commit)
  - Internal calls: `ctx_repo_path_root()`, `git_last_tag()`, `git_first_commit_id()`, `git_last_commit_id()`, `bh.run_output()`, `ih.splitlines()`

- **`git_unpushed_commits(path='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of any local commits that have not been pushed
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of unpushed commit strings
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `ih.splitlines()`

- **`git_untracked_files(path='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of any local files that are not tracked in the git repo
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of untracked file paths
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `ih.splitlines()`

- **`git_stashlist(path='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of any local stashes
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of stash entries
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `ih.splitlines()`

- **`git_status(path='', debug=False, timeout=None, exception=False, show=False)`** - Return a list of any modified or untracked files
  - `path`: Path to git repo, if not using current working directory
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of status entries
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `ih.splitlines_and_strip()`

- **`git_info_dict(path='', fetch=False, debug=False, timeout=None, exception=False, show=False)`** - Return a dict of info about the repo
  - `path`: Path to git repo, if not using current working directory
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Dictionary with keys: `path_root`, `url`, `branch`, `branch_date`, `branch_tracking`, `branch_tracking_date`, `last_tag`, `status`, `stashes`, `unpushed`, `commits_since_last_tag`
  - Internal calls: `ctx_repo_path_root()`, `git_repo_path_root()`, `git_origin_url()`, `git_current_branch()`, `git_branch_date()`, `git_current_tracking_branch()`, `git_last_tag()`, `git_status()`, `git_stashlist()`, `git_unpushed_commits()`, `git_commits_since_last_tag()`

- **`git_info_string(path='', fetch=False, debug=False, timeout=None, exception=False, show=False)`** - Build up a string of info from git_info_dict and return it
  - `path`: Path to git repo, if not using current working directory
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: Formatted string with git repository information
  - Internal calls: `ctx_repo_path_root()`, `git_info_dict()`

- **`git_branch_date(path='', branch='', fetch=False, debug=False, timeout=None, exception=False, show=False)`** - Return datetime string (and relative age) of branch
  - `path`: Path to git repo, if not using current working directory
  - `branch`: Name of branch (prefix with 'origin/' for remote branch)
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: String with date and relative time
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`

- **`git_remote_branches(path='', fetch=False, grep='', include_times=False, debug=False, timeout=None, exception=False, show=False)`** - Return list of remote branch names or list of dicts (via `git ls-remote --heads`)
  - `path`: Path to git repo, if not using current working directory
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `grep`: `grep -iE` pattern to filter branches by (case-insensitive)
  - `include_times`: Include info from git_branch_date in results if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of branch names or list of dicts (alphabetized if include_times=False, otherwise ordered by most recent commit)
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `bh.tools.grep_output()`, `_dates_for_branches()`

- **`git_local_branches(path='', fetch=False, grep='', include_times=False, debug=False, timeout=None, exception=False, show=False)`** - Return list of local branch names or list of dicts (via `git branch`)
  - `path`: Path to git repo, if not using current working directory
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `grep`: `grep -iE` pattern to filter branches by (case-insensitive)
  - `include_times`: Include info from git_branch_date in results if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of branch names or list of dicts (alphabetized if include_times=False, otherwise ordered by most recent commit)
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `bh.tools.grep_output()`, `_dates_for_branches()`

- **`git_remote_branches_merged_with(path='', branch='develop', fetch=False, include_times=False, debug=False, timeout=None, exception=False, show=False)`** - Return a list of branches on origin that have been merged with branch
  - `path`: Path to git repo, if not using current working directory
  - `branch`: Remote branch name (without leading 'origin/')
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `include_times`: Include info from git_branch_date in results if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of merged branch names or list of dicts
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `bh.tools.grep_output()`, `_dates_for_branches()`

- **`git_local_branches_merged_with(path='', branch='develop', fetch=False, include_times=False, debug=False, timeout=None, exception=False, show=False)`** - Return a list of local branches that have been merged with branch
  - `path`: Path to git repo, if not using current working directory
  - `branch`: Local branch name
  - `fetch`: Call git_fetch func before calling the generated `git` command if True
  - `include_times`: Include info from git_branch_date in results if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if git command has error if True
  - `show`: Display git commands before executing if True
  - Returns: List of merged branch names or list of dicts
  - Internal calls: `ctx_repo_path_root()`, `bh.run_output()`, `bh.tools.grep_output()`, `_dates_for_branches()`

### Docker Operations (`bh.tools.*`)

Docker functions provide container lifecycle management with service-specific shortcuts and platform adaptation.

- **`docker_ok(exception=False)`** - Check if Docker daemon is available and running
  - `exception`: Raise exception if Docker unavailable and True
  - Returns: Boolean indicating Docker availability
  - Internal calls: `bh.run_output()`

- **`docker_stop(name, kill=False, signal='KILL', rm=False, exception=False, show=False)`** - Return True if successfully stopped
  - `name`: Name of the container
  - `kill`: Kill the container instead of stopping if True
  - `signal`: Signal to send to the container if kill is True
  - `rm`: Remove the container after stop/kill if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - Returns: Boolean success status
  - Internal calls: `docker_ok()`, `bh.run_output()`

- **`docker_start_or_run(name, image='', command='', detach=True, rm=False, interactive=False, ports='', volumes='', platform='', env_vars={}, exception=False, show=False, force=False)`** - Start existing container or create/run container
  - `name`: Name for the container
  - `image`: Image to use (i.e. image:tag)
  - `command`: Command to run in the container
  - `detach`: Run container in the background if True (set to False if interactive is True)
  - `rm`: Automatically delete the container when it exits if True
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `ports`: String containing {host-port}:{container-port} pairs separated by , ; |
  - `volumes`: String containing {host-path}:{container-path} pairs separated by , ; |
  - `platform`: Platform to set if server is multi-platform capable
  - `env_vars`: Dict of environment variables and values to set
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - Returns: Boolean success status
  - Internal calls: `docker_ok()`, `docker_stop()`, `ih.string_to_list()`, `bh.run()`, `bh.run_output()`

- **`docker_container_id(name)`** - Return the container ID for running container name
  - `name`: Name of the container
  - Returns: String container ID or empty string
  - Internal calls: `docker_ok()`, `bh.run_output()`

- **`docker_container_inspect(name, exception=False, show=False)`** - Return detailed information on specified container as a list
  - `name`: Name of the container
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker command and output if True
  - Returns: List of container information dictionaries
  - Internal calls: `docker_ok()`, `bh.run_output()`

- **`docker_container_config(name, exception=False, show=False)`** - Return dict of config information for specified container (from inspect)
  - `name`: Name of the container
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker command and output if True
  - Returns: Dictionary of container configuration
  - Internal calls: `docker_container_inspect()`

- **`docker_container_env_vars(name, exception=False, show=False)`** - Return dict of environment vars for specified container
  - `name`: Name of the container
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker command and output if True
  - Returns: Dictionary of environment variables
  - Internal calls: `docker_container_config()`

- **`docker_logs(name, num_lines=None, follow=False, details=False, since='', until='', timestamps=False, show=False)`** - Show logs on an existing container
  - `name`: Name of the container
  - `num_lines`: Number of lines to show from the end of the logs
  - `follow`: Follow log output if True
  - `details`: Show extra details provided to logs if True
  - `since`: Show logs since timestamp (iso format or relative)
  - `until`: Show logs before timestamp (iso format or relative)
  - `timestamps`: Show timestamps if True
  - `show`: Show the docker command and output if True
  - Returns: Exit code or log output
  - Internal calls: `docker_ok()`, `bh.run()`, `bh.run_output()`

- **`docker_exec(name, command='pwd', output=False, env_vars={}, show=False)`** - Run shell command on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `command`: Command to execute
  - `output`: Return output or error from command if True; otherwise return exit status
  - `env_vars`: Dict of environment variables and values to set
  - `show`: Show the docker command and output if True
  - Returns: Command output or exit status
  - Internal calls: `docker_ok()`, `docker_start_or_run()`, `bh.run_output()`, `bh.run()`

- **`docker_exec_wait(name, command='pwd', sleeptime=2, env_vars={}, show=False)`** - Wait for a shell command to succeed in an existing container (will be started if stopped)
  - `name`: Name of the container
  - `command`: Command to execute
  - `sleeptime`: Time to sleep between checks
  - `env_vars`: Dict of environment variables and values to set
  - `show`: Show the docker command and output if True
  - Returns: None (blocks until command succeeds)
  - Internal calls: `docker_exec()`

- **`docker_shell(name, shell='sh', env_vars={}, show=False)`** - Start shell on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `shell`: Name of shell to execute
  - `env_vars`: Dict of environment variables and values to set
  - `show`: Show the docker command and output if True
  - Returns: Exit code
  - Internal calls: `docker_ok()`, `docker_start_or_run()`, `bh.run()`

- **`docker_cleanup_volumes(exception=False, show=False)`** - Use this when creating a container fails with 'No space left on device'
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker command and output if True
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

#### Database Service Functions

- **`docker_redis_start(name, version='6-alpine', port=6300, data_dir=None, aof=True, interactive=False, rm=False, exception=False, show=False, force=False)`** - Start or create redis container
  - `name`: Name for the container
  - `version`: Redis image version
  - `port`: Port to map into the container
  - `data_dir`: Directory that will map to container's /data (absolute path or subdirectory of current directory)
  - `aof`: Use appendonly.aof file if True
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

- **`docker_redis_cli(name, show=False)`** - Start redis-cli on an existing container (will be started if stopped)
  - `name`: Name for the container
  - `show`: Show the docker command and output if True
  - Returns: Exit code
  - Internal calls: `docker_shell()`

- **`docker_mongo_start(name, version='4.4', port=27000, username='mongouser', password='some.pass', data_dir=None, interactive=False, rm=False, exception=False, show=False, force=False, wait=False, sleeptime=2)`** - Start or create mongo container
  - `name`: Name for the container
  - `version`: Mongo image version
  - `port`: Port to map into the container
  - `username`: Username to set for root user on first run
  - `password`: Password to set for root user on first run
  - `data_dir`: Directory that will map to container's /data/db (absolute path or subdirectory of current directory)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - `wait`: Don't return until mongo is able to accept connections if True
  - `sleeptime`: If wait is True, sleep this number of seconds before checks
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

- **`docker_mongo_cli(name, show=False)`** - Start mongo on an existing container (will be started if stopped)
  - `name`: Name for the container
  - `show`: Show the docker command and output if True
  - Returns: Exit code
  - Internal calls: `docker_container_env_vars()`, `docker_shell()`

- **`docker_mongo_wait(name, sleeptime=2, show=False)`** - Wait for mongo on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `sleeptime`: Time to sleep between checks
  - `show`: Show the docker command and output if True
  - Returns: None (blocks until postgres is ready)
  - Internal calls: `docker_container_env_vars()`, `docker_exec_wait()`

- **`docker_postgres_start(name, version='13-alpine', port=5400, username='postgresuser', password='some.pass', db='postgresdb', data_dir=None, interactive=False, rm=False, exception=False, show=False, force=False, wait=False, sleeptime=2)`** - Start or create postgres container
  - `name`: Name for the container
  - `version`: Postgres image version
  - `port`: Port to map into the container
  - `username`: Username to set as superuser on first run
  - `password`: Password to set for superuser on first run
  - `db`: Name of default database
  - `data_dir`: Directory that will map to container's /var/lib/postgresql/data (absolute path or subdirectory of current directory)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - `wait`: Don't return until postgres is able to accept connections if True
  - `sleeptime`: If wait is True, sleep this number of seconds before checks
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`, `docker_postgres_wait()`

- **`docker_postgres_cli(name, show=False)`** - Start psql on an existing container (will be started if stopped)
  - `name`: Name for the container
  - `show`: Show the docker command and output if True
  - Returns: Exit code
  - Internal calls: `docker_container_env_vars()`, `docker_shell()`

- **`docker_postgres_wait(name, sleeptime=2, show=False)`** - Wait for psql on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `sleeptime`: Time to sleep between checks
  - `show`: Show the docker command and output if True
  - Returns: None (blocks until postgres is ready)
  - Internal calls: `docker_container_env_vars()`, `docker_exec_wait()`

- **`docker_mysql_start(name, version='8.0', port=3300, root_password='root.pass', username='mysqluser', password='some.pass', db='mysqldb', data_dir=None, interactive=False, rm=False, exception=False, show=False, force=False, wait=False, sleeptime=2)`** - Start or create mysql container
  - `name`: Name for the container
  - `version`: MySQL image version (or mysql/mysql-server for Mac M1)
  - `port`: Port to map into the container
  - `root_password`: Password to set for the root superuser account
  - `username`: Username to set as superuser on first run
  - `password`: Password to set for superuser on first run
  - `db`: Name of default database
  - `data_dir`: Directory that will map to container's /var/lib/mysql (absolute path or subdirectory of current directory)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - `wait`: Don't return until mysql is able to accept connections if True
  - `sleeptime`: If wait is True, sleep this number of seconds before checks
  - Returns: Boolean success status
  - Internal calls: `bh.run_output()`, `docker_start_or_run()`, `docker_mysql_wait()`

- **`docker_mysql_cli(name, show=False)`** - Start mysql on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `show`: Show the docker command and output if True
  - Returns: Exit code
  - Internal calls: `docker_container_env_vars()`, `docker_shell()`

- **`docker_mysql_wait(name, sleeptime=2, show=False)`** - Wait for mysql on an existing container (will be started if stopped)
  - `name`: Name of the container
  - `sleeptime`: Time to sleep between checks
  - `show`: Show the docker command and output if True
  - Returns: None (blocks until mysql is ready)
  - Internal calls: `docker_container_env_vars()`, `docker_exec_wait()`

#### OS Container Functions

- **`docker_alpine_start(name, version='3.12', command='sleep 86400', detach=True, interactive=False, rm=False, exception=False, show=False, force=False)`** - Start or create alpine container
  - `name`: Name for the container
  - `version`: Alpine image version
  - `command`: Command to run (default is sleep for a day)
  - `detach`: Run container in the background if True (set to False if interactive is True)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

- **`docker_ubuntu_start(name, version='18.04', command='sleep 86400', detach=True, interactive=False, rm=False, exception=False, show=False, force=False)`** - Start or create ubuntu container
  - `name`: Name for the container
  - `version`: Ubuntu image version
  - `command`: Command to run (default is sleep for a day)
  - `detach`: Run container in the background if True (set to False if interactive is True)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

- **`docker_fedora_start(name, version='33', command='sleep 86400', detach=True, interactive=False, rm=False, exception=False, show=False, force=False)`** - Start or create fedora container
  - `name`: Name for the container
  - `version`: Fedora image version
  - `command`: Command to run (default is sleep for a day)
  - `detach`: Run container in the background if True (set to False if interactive is True)
  - `interactive`: Keep STDIN open and allocate pseudo-TTY if True
  - `rm`: Automatically delete the container when it exits if True
  - `exception`: Raise exception if docker has error response and True
  - `show`: Show the docker commands and output if True
  - `force`: Stop the container and remove it before re-creating if True
  - Returns: Boolean success status
  - Internal calls: `docker_start_or_run()`

### SSH Operations (`bh.tools.*`)

SSH functions provide remote system access with connection management and key discovery.

- **`ssh_to_server(ip_or_hostname, user=None, pem_file=None, private_key_file=None, command='', timeout=None, verbose=False)`** - Actually SSH to a server and run a command or start interactive session
  - `ip_or_hostname`: IP address or hostname of server
  - `user`: Remote SSH user
  - `pem_file`: Absolute path to pem file
  - `private_key_file`: Absolute path to private key file
  - `command`: Optional command to run on the remote server (if specified, output is returned; if not, session is interactive)
  - `timeout`: Number of seconds to wait for a specified command to run on the remote server
  - `verbose`: Print the generated SSH command and result if True
  - Returns: Command output if command specified, otherwise exit code
  - Internal calls: `ssh_configured_hosts()`, `bh.run_output()`, `bh.run()`

- **`ssh_pem_files()`** - Find all .pem files in ~/.ssh and return a dict with absolute paths
  - Returns: Dictionary mapping filename (without extension) to absolute path
  - Internal calls: `fh.strip_extension()`

- **`ssh_private_key_files()`** - Find all private key files in ~/.ssh and return a dict with absolute paths
  - Returns: Dictionary mapping filename (without extension) to absolute path
  - Internal calls: `fh.strip_extension()`

- **`ssh_configured_hosts()`** - Return a set of Hosts from the ~/.ssh/config file
  - Returns: Set of configured host names
  - Internal calls: `fh.abspath()`

- **`ssh_determine_aws_user_for_server(ip_or_hostname, pem_file, verbose=False)`** - Determine which AWS default user is setup for server
  - `ip_or_hostname`: IP address or hostname of server
  - `pem_file`: Absolute path to pem file
  - `verbose`: Show info for each attempt if True
  - Returns: String username if found, otherwise None
  - Internal calls: `ssh_to_server()`

### Grep Operations (`bh.tools.*`)

Enhanced text search with pattern matching capabilities.

- **`grep_output(output, pattern=None, regex=None, ignore_case=True, invert=False, lines_before_match=None, lines_after_match=None, results_as_string=False, join_result_string_on='\n', strip_whitespace=False, no_filename=False, line_number=False, only_matching=False, byte_offset=False, suppress_errors=True, extra_pipe=None, show=False)`** - Use grep to match lines of output against pattern
  - `output`: Some output you would be piping to grep in a shell environment
  - `pattern`: Grep pattern string (extended `-E` style allowed)
  - `regex`: Compiled regular expression (from re.compile) or string that can be passed to re.compile
  - `ignore_case`: Ignore case (`grep -i` or re.IGNORECASE) if True
  - `invert`: Select non-matching items (`grep -v`) if True (only applied when using pattern, not regex)
  - `lines_before_match`: Number of context lines to show before match (only applied when using pattern, not regex)
  - `lines_after_match`: Number of context lines to show after match (only applied when using pattern, not regex)
  - `results_as_string`: Return a string instead of a list of strings if True
  - `join_result_string_on`: Character or string to join a list of strings on
  - `strip_whitespace`: Strip trailing and leading whitespace for results if True
  - `no_filename`: Do not prefix matching lines with their corresponding file names if True (only applied when using pattern, not regex)
  - `line_number`: Prefix matching lines with line number within its input file if True (only applied when using pattern, not regex)
  - `only_matching`: Print only the matched parts of a matching line if True (only applied when using pattern, not regex)
  - `byte_offset`: Print the byte offset within the input file before each line of output if True (only applied when using pattern, not regex)
  - `suppress_errors`: Suppress error messages about nonexistent or unreadable files if True (only applied when using pattern, not regex)
  - `extra_pipe`: String containing other command(s) to pipe grepped output to (only applied when using pattern, not regex)
  - `show`: Show the `grep` command before executing if True (only applied when using pattern, not regex)
  - Returns: List of strings (split on newline) or string if results_as_string=True
  - Internal calls: `_prep_common_grep_args()`, `bh.run_output()`, `ih.splitlines()`, `ih.splitlines_and_strip()`

- **`grep_path(pattern, path='', recursive=True, ignore_case=True, invert=False, lines_before_match=None, lines_after_match=None, exclude_files=None, exclude_dirs=None, results_as_string=False, join_result_string_on='\n', strip_whitespace=False, no_filename=False, line_number=False, only_matching=False, byte_offset=False, suppress_errors=True, extra_pipe=None, color=False, show=False)`** - Use grep to match lines in files at a path against pattern
  - `pattern`: Grep pattern string (extended `-E` style allowed)
  - `path`: Path to directory where the search should be started, if not using current working directory
  - `recursive`: Use `-R` to search all files at path if True
  - `ignore_case`: Ignore case (`grep -i`) if True
  - `invert`: Select non-matching items (`grep -v`) if True
  - `lines_before_match`: Number of context lines to show before match
  - `lines_after_match`: Number of context lines to show after match
  - `exclude_files`: List of file names and patterns to exclude from searching or string separated by , ; |
  - `exclude_dirs`: List of dir names and patterns to exclude from searching or string separated by , ; |
  - `results_as_string`: Return a string instead of a list of strings if True
  - `join_result_string_on`: Character or string to join a list of strings on
  - `strip_whitespace`: Strip trailing and leading whitespace for results if True
  - `no_filename`: Do not prefix matching lines with their corresponding file names if True
  - `line_number`: Prefix matching lines with line number within its input file if True
  - `only_matching`: Print only the matched parts of a matching line if True
  - `byte_offset`: Print the byte offset within the input file before each line of output if True
  - `suppress_errors`: Suppress error messages about nonexistent or unreadable files if True
  - `extra_pipe`: String containing other command(s) to pipe grepped output to
  - `color`: Will invoke the generated grep command with `bh.run` (output will not be captured) if True
  - `show`: Show the `grep` command before executing if True
  - Returns: List of strings or string if results_as_string=True, or exit code if color=True
  - Internal calls: `fh.abspath()`, `_prep_common_grep_args()`, `bh.run()`, `bh.run_output()`, `ih.splitlines()`, `ih.splitlines_and_strip()`

- **`grep_path_count(pattern, path='', recursive=True, ignore_case=True, invert=False, exclude_files=None, exclude_dirs=None, suppress_errors=True, results_as_string=False, join_result_string_on='\n', show=False)`** - Use grep to count the match lines in files at a path against pattern
  - `pattern`: Grep pattern string (extended `-E` style allowed)
  - `path`: Path to directory where the search should be started, if not using current working directory
  - `recursive`: Use `-R` to search all files at path if True
  - `ignore_case`: Ignore case (`grep -i`) if True
  - `invert`: Select non-matching items (`grep -v`) if True
  - `exclude_files`: List of file names and patterns to exclude from searching or string separated by , ; |
  - `exclude_dirs`: List of dir names and patterns to exclude from searching or string separated by , ; |
  - `suppress_errors`: Suppress error messages about nonexistent or unreadable files if True
  - `results_as_string`: Return a string instead of a list of tuples if True
  - `join_result_string_on`: Character or string to join a list of strings on
  - `show`: Show the `grep` command before executing if True
  - Returns: List of 2-item tuples (filename, count) sorted by count descending then filename ascending
  - Internal calls: `fh.abspath()`, `_prep_common_grep_args()`, `bh.run_output()`

- **`grep_path_count_dirs(pattern, path='', recursive=True, ignore_case=True, invert=False, exclude_files=None, exclude_dirs=None, suppress_errors=True, results_as_string=False, join_result_string_on='\n', show=False)`** - Use grep to count match lines in files against pattern, aggregated by dir
  - `pattern`: Grep pattern string (extended `-E` style allowed)
  - `path`: Path to directory where the search should be started, if not using current working directory
  - `recursive`: Use `-R` to search all files at path if True
  - `ignore_case`: Ignore case (`grep -i`) if True
  - `invert`: Select non-matching items (`grep -v`) if True
  - `exclude_files`: List of file names and patterns to exclude from searching or string separated by , ; |
  - `exclude_dirs`: List of dir names and patterns to exclude from searching or string separated by , ; |
  - `suppress_errors`: Suppress error messages about nonexistent or unreadable files if True
  - `results_as_string`: Return a string instead of a list of tuples if True
  - `join_result_string_on`: Character or string to join a list of strings on
  - `show`: Show the `grep` command before executing if True
  - Returns: List of 2-item tuples (dirname, count) sorted by count descending then dirname ascending
  - Internal calls: `fh.abspath()`, `_prep_common_grep_args()`, `bh.run_output()`

- **`grep_select_vim(pattern, path='', recursive=True, ignore_case=True, invert=False, lines_before_match=None, lines_after_match=None, exclude_files=None, exclude_dirs=None, suppress_errors=True, open_all_together=False)`** - Use grep to find files, then present a menu of results and line numbers
  - `pattern`: Grep pattern string (extended `-E` style allowed)
  - `path`: Path to directory where the search should be started, if not using current working directory
  - `recursive`: Use `-R` to search all files at path if True
  - `ignore_case`: Ignore case (`grep -i`) if True
  - `invert`: Select non-matching items (`grep -v`) if True
  - `lines_before_match`: Number of context lines to show before match
  - `lines_after_match`: Number of context lines to show after match
  - `exclude_files`: List of file names and patterns to exclude from searching or string separated by , ; |
  - `exclude_dirs`: List of dir names and patterns to exclude from searching or string separated by , ; |
  - `suppress_errors`: Suppress error messages about nonexistent or unreadable files if True
  - `open_all_together`: Don't open each individual file to the line number, just open them all in the same vim session if True
  - Returns: None (opens selected files in vim)
  - Internal calls: `fh.abspath()`, `_prep_common_grep_args()`, `bh.run_output()`, `ih.splitlines()`, `ih.make_selections()`, `bh.run()`

### Pip Operations (`bh.tools.*`)

Python package management utilities.

- **`installed_packages(name_only=False)`** - Return a dict or list of installed packages from importlib_metadata.distributions
  - `name_only`: Return a list of package names only if True
  - Returns: Dictionary mapping package names to versions, or list of package names if name_only=True
  - Internal calls: None

- **`installed_packages_by_dir()`** - Return a dict of installed packages from importlib_metadata.distributions
  - Returns: Dictionary with 'standard' key (dict of standard packages and versions) and 'other' key (dict of packages installed outside of PATH_TO_SITE_PACKAGES)
  - Internal calls: None

- **`installed_packages_non_site_packages()`** - Return a dict of installed packages from importlib_metadata.distributions
  - Returns: Dictionary of packages not in PATH_TO_SITE_PACKAGES mapped to their paths
  - Internal calls: None

- **`pip_freeze(pip_path='', venv_only=True, debug=False, timeout=None, exception=True, show=False)`** - Run pip freeze command
  - `pip_path`: Absolute path to pip in a virtual environment (use derived PATH_TO_PIP if not specified)
  - `venv_only`: Only run pip if it's in a venv if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if pip command has error if True
  - `show`: Show the `pip` command before executing if True
  - Returns: Exit code
  - Internal calls: `bh.run()`

- **`pip_install_editable(paths, pip_path='', venv_only=True, debug=False, timeout=None, exception=True, show=False)`** - Pip install the given paths in "editable mode"
  - `paths`: Local paths to projects to install in "editable mode" (list of strings OR string separated by , ; |)
  - `pip_path`: Absolute path to pip in a virtual environment (use derived PATH_TO_PIP if not specified)
  - `venv_only`: Only run pip if it's in a venv if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `timeout`: Seconds to wait before stopping commands
  - `exception`: Raise exception if pip command has error if True
  - `show`: Show the `pip` command before executing if True
  - Returns: Exit code
  - Internal calls: `ih.get_list_from_arg_strings()`, `bh.run()`

- **`pip_extras(package_name, venv_only=True, exception=True)`** - Return the extras_requires keys for specified package
  - `package_name`: Name of the package to get extras_requires keys
  - `venv_only`: Only run pip if it's in a venv if True
  - `exception`: Raise exception if pip command has error if True
  - Returns: List of extras keys or None
  - Internal calls: None

- **`pip_version(pip_path='', venv_only=True, debug=False, exception=True)`** - Return a tuple for the pip version (major int, minor int, patch string)
  - `pip_path`: Absolute path to pip in a virtual environment (use derived PATH_TO_PIP if not specified)
  - `venv_only`: Only run pip if it's in a venv if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `exception`: Raise exception if pip command has error if True
  - Returns: Tuple (major, minor, patch)
  - Internal calls: `bh.run_output()`, `bh.tools.grep_output()`, `ih.string_to_version_tuple()`

- **`pip_package_versions_available(package_name, pip_path='', venv_only=True, debug=False, exception=True)`** - Return a list of versions available on pypi for the given package
  - `package_name`: Name of the package on pypi.org
  - `pip_path`: Absolute path to pip in a virtual environment (use derived PATH_TO_PIP if not specified)
  - `venv_only`: Only run pip if it's in a venv if True
  - `debug`: Insert breakpoint before subprocess calls if True
  - `exception`: Raise exception if pip command has error if True
  - Returns: List of available version strings
  - Internal calls: `pip_version()`, `bh.run_output()`, `bh.tools.grep_output()`

### Process Operations (`bh.tools.*`)

Process management utilities.

- **`ps_output()`** - Return a list of dicts containing info about current running processes
  - Returns: List of dictionaries with process information
  - Internal calls: `bh.run_output()`, `PsOutputMatcher` (from input_helper)

### Python Environment Operations (`bh.tools.*`)

Python environment management through pyenv.

- **`pyenv_install_python_version(*versions)`** - Use pyenv to install versions of Python
  - `versions`: List of versions to install (can also be a list of versions contained in a single string, separated by , ; |)
  - Returns: List of tuples (version, success_boolean)
  - Internal calls: `ih.get_list_from_arg_strings()`, `bh.run()`

- **`pyenv_update(show=True)`** - Update pyenv
  - `show`: Show the command before executing if True
  - Returns: Boolean success status
  - Internal calls: `bh.run()`, `bh.tools.git_repo_update()`

- **`pyenv_get_installable_versions(only_py3=True, only_latest_per_group=True, only_released=True, only_non_released=False)`** - Return a list of Python versions that can be installed to ~/.pyenv/versions
  - `only_py3`: Only list standard Python 3.x versions if True
  - `only_latest_per_group`: Only include the latest version per group if True
  - `only_released`: Only include released versions, not alpha/beta/rc/dev/src if True
  - `only_non_released`: Only include non-released versions, like alpha/beta/rc/dev/src if True
  - Returns: List of installable Python version strings
  - Internal calls: `bh.run_output()`, `bh.tools.grep_output()`, `ih.splitlines_and_strip()`

- **`pyenv_select_python_versions_to_install(only_py3=True, only_latest_per_group=True, only_released=True, only_non_released=False)`** - Select versions of Python to install with pyenv
  - `only_py3`: Only select from standard Python 3.x versions if True
  - `only_latest_per_group`: Only include the latest version per group if True
  - `only_released`: Only include released versions, not alpha/beta/rc/dev/src if True
  - `only_non_released`: Only include non-released versions, like alpha/beta/rc/dev/src if True
  - Returns: List of tuples (version, success_boolean) from installation
  - Internal calls: `pyenv_get_installable_versions()`, `ih.make_selections()`, `pyenv_install_python_version()`

- **`pyenv_get_versions()`** - Return a list of Python versions locally installed to ~/.pyenv/versions
  - Returns: List of installed Python version strings
  - Internal calls: None

- **`pyenv_path_to_python_version(version)`** - Return path to the installed Python binary for the given version or None
  - `version`: Python version string
  - Returns: String path to Python binary or None
  - Internal calls: None

- **`pyenv_pip_versions(py_versions='')`** - Return a dict of default pip versions for each given Python version
  - `py_versions`: String containing locally installed Python versions separated by , ; | (if none specified, use all local versions)
  - Returns: Dictionary mapping Python versions to pip version tuples
  - Internal calls: `ih.get_list_from_arg_strings()`, `pyenv_get_versions()`, `bh.tools.pip_version()`

- **`pyenv_pip_package_versions_available(package_name, py_versions='', show=False)`** - Return a dict of package versions available on pypi for the given package
  - `package_name`: Name of the package on pypi.org
  - `py_versions`: String containing locally installed Python versions separated by , ; | (if none specified, use all local versions)
  - `show`: Display the results if True
  - Returns: Dictionary mapping Python versions to lists of available package versions
  - Internal calls: `ih.get_list_from_arg_strings()`, `pyenv_get_versions()`, `bh.tools.pip_package_versions_available()`

- **`pyenv_create_venvs_for_py_versions_and_dep_versions(base_dir, py_versions='', pip_version='', pip_latest=False, wheel_version='', wheel_latest=False, clean=False, die=False, local_package_paths='', extra_packages='', dep_versions_dict=None)`** - Create a combination of venvs for the given py_versions and dep_versions
  - `base_dir`: Path to directory where the venvs will be created
  - `py_versions`: String containing Python versions to make venvs for separated by , ; | (if none specified, use all local versions)
  - `pip_version`: Specific version of pip to install first
  - `pip_latest`: Install latest version of pip if True (ignored if pip_version specified)
  - `wheel_version`: Specific version of wheel to install first
  - `wheel_latest`: Install latest version of wheel if True (ignored if wheel_version specified)
  - `clean`: Delete any existing venv that would be created if it exists if True
  - `die`: Return if any part of venv creation or pip install fails if True
  - `local_package_paths`: Local paths to projects to install in "editable mode" (may be a list or string separated by , ; |)
  - `extra_packages`: String of extra packages to be installed in each venv (may be a list or string separated by , ; |)
  - `dep_versions_dict`: Dict where keys are package names and values are specific versions (versions may be a list or string separated by , ; |)
  - Returns: None (creates virtual environments)
  - Internal calls: `fh.abspath()`, `ih.get_list_from_arg_strings()`, `pyenv_get_versions()`, `pyenv_path_to_python_version()`, `pyenv_install_python_version()`, `bh.run()`

## Basic Examples

```
% ipython
...

In [1]: import bg_helper as bh

In [2]: def lame():
   ...:     return 1/0

In [3]: def blah(*args, **kwargs):
   ...:     return locals()

In [4]: bh.call_func(blah)
Out[4]:
{'args': '()',
 'func_name': 'blah',
 'kwargs': '{}',
 'status': 'ok',
 'value': {'args': (), 'kwargs': {}}}

In [5]: bh.call_func(blah, 'cats', 'dogs')
Out[5]:
{'args': "('cats', 'dogs')",
 'func_name': 'blah',
 'kwargs': '{}',
 'status': 'ok',
 'value': {'args': ('cats', 'dogs'), 'kwargs': {}}}

In [6]: bh.call_func(blah, 'cats', 'dogs', meh=[1, 2, 3, 4, 5])
Out[6]:
{'args': "('cats', 'dogs')",
 'func_name': 'blah',
 'kwargs': "{'meh': [1, 2, 3, 4, 5]}",
 'status': 'ok',
 'value': {'args': ('cats', 'dogs'), 'kwargs': {'meh': [1, 2, 3, 4, 5]}}}

In [7]: bh.call_func(lame)
======================================================================
2017-04-01 12:32:35,107: func=lame args=() kwargs={}
Traceback (most recent call last):
  File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func
    value = func(*args, **kwargs)
  File "<ipython-input-2-ac0fa5de647a>", line 2, in lame
    return 1/0
ZeroDivisionError: division by zero

Out[7]:
{'args': '()',
 'error_type': "<class 'ZeroDivisionError'>",
 'error_value': "ZeroDivisionError('division by zero',)",
 'fqdn': 'x200-purple',
 'func_doc': None,
 'func_module': '__main__',
 'func_name': 'lame',
 'kwargs': '{}',
 'status': 'error',
 'time_epoch': 1491067955.1004958,
 'time_string': '2017_0401-Sat-123235',
 'traceback_string': 'Traceback (most recent call last):\n  File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func\n    value = func(*args, **kwargs)\n  File "<ipython-input-2-ac0fa5de647a>", line 2, in lame\n    return 1/0\nZeroDivisionError: division by zero\n'}

In [8]: cat log--bg-helper.log
2017-04-01 12:32:35,107 - ERROR - call_func: func=lame args=() kwargs={}
Traceback (most recent call last):
  File "/tmp/here/venv/lib/python3.5/site-packages/bg_helper/__init__.py", line 70, in call_func
    value = func(*args, **kwargs)
  File "<ipython-input-2-ac0fa5de647a>", line 2, in lame
    return 1/0
ZeroDivisionError: division by zero

In [9]: bh.SimpleBackgroundTask('echo "hello from console" > /tmp/blahblah.txt')
Out[9]: <bg_helper.SimpleBackgroundTask at 0x7ff112229c18>

In [10]: ls /tmp/blahblah.txt
/tmp/blahblah.txt

In [11]: cat /tmp/blahblah.txt
hello from console

In [12]: bh.SimpleBackgroundTask('echo "$(date)" >> /tmp/blahblah.txt')
Out[12]: <bg_helper.SimpleBackgroundTask at 0x7ff110057cf8>

In [13]: cat /tmp/blahblah.txt
hello from console
Sat Apr  1 12:33:23 CDT 2017
```
