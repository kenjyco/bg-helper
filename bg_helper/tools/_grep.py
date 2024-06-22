__all__ = [
    'grep_output', 'grep_select_vim'
]

import re
import bg_helper as bh
import fs_helper as fh
import input_helper as ih
from os import getcwd, listdir
from os.path import isfile


def _prep_common_grep_args(pattern=None, ignore_case=True, invert=False,
                           lines_before_match=None, lines_after_match=None,
                           exclude_files=None, exclude_dirs=None,
                           no_filename=False, line_number=False,
                           only_matching=False, byte_offset=False):
    """Return the common args that should be passed to grep based on kwargs set

    - pattern: grep pattern string (extended `-E` style allowed)
    - ignore_case: if True, ignore case (`grep -i` or re.IGNORECASE)
    - invert: if True, select non-matching items (`grep -v`)
    - lines_before_match: number of context lines to show before match
        - will not be used if `invert=True`
    - lines_after_match: number of context lines to show after match
        - will not be used if `invert=True`
    - exclude_files: list of file names and patterns to exclude from searching
        - or string separated by any of , ; |
    - exclude_dirs: list of dir names and patterns to exclude from searching
        - or string separated by any of , ; |
    - no_filename: if True, do not prefix matching lines with their corresponding
      file names
    - line_number: if True, prefix matching lines with line number within its
      input file
    - only_matching: if True, print only the matched parts of a matching line
    - byte_offset: if True, print the byte offset within the input file before each
      line of output
        - if `only_matching=True`, print the offset of the matching part itself
    """
    assert pattern, "The grep 'pattern' is required (extended `-E` style allowed)"
    grep_args = '-'
    if ignore_case:
        grep_args += 'i'
    if no_filename:
        grep_args += 'h'
    if line_number:
        grep_args += 'n'
    if only_matching:
        grep_args += 'o'
    if byte_offset:
        grep_args += 'b'

    if invert:
        grep_args += 'v'
    else:
        if grep_args == '-':
            grep_args = ''
        if lines_before_match:
            grep_args = '-B {} '.format(lines_before_match) + grep_args
        if lines_after_match:
            grep_args = '-A {} '.format(lines_after_match) + grep_args

    if exclude_files:
        exclude_files = ih.get_list_from_arg_strings(exclude_files)
        grep_args += ' ' + ' '.join([
            '--exclude={}'.format(repr(f))
            for f in exclude_files
        ])
    if exclude_dirs:
        exclude_dirs = ih.get_list_from_arg_strings(exclude_dirs)
        grep_args += ' ' + ' '.join([
            '--exclude-dir={}'.format(repr(d))
            for d in exclude_dirs
        ])

    if '(' in pattern and '|' in pattern and ')' in pattern:
        grep_args += ' -E {}'.format(repr(pattern))
    else:
        grep_args += ' {}'.format(repr(pattern))

    return grep_args.strip()


def grep_output(output, pattern=None, regex=None, ignore_case=True, invert=False,
                lines_before_match=None, lines_after_match=None,
                results_as_string=False, join_result_string_on='\n',
                strip_whitespace=False, extra_pipe=None, show=False):
    """Use grep to match lines of output against pattern

    - output: some output you would be piping to grep in a shell environment
    - pattern: grep pattern string (extended `-E` style allowed)
    - regex: a compiled regular expression (from re.compile)
        - or a string that can be passed to re.compile
        - if match groups are used, the group matches will be returned
    - ignore_case: if True, ignore case (`grep -i` or re.IGNORECASE)
    - invert: if True, select non-matching items (`grep -v`)
        - only applied when using pattern, not regex
    - lines_before_match: number of context lines to show before match
        - only applied when using pattern, not regex
        - will not be used if `invert=True`
    - lines_after_match: number of context lines to show after match
        - only applied when using pattern, not regex
        - will not be used if `invert=True`
    - results_as_string: if True, return a string instead of a list of strings
    - join_result_string_on: character or string to join a list of strings on
        - only applied if `results_as_string=True`
    - strip_whitespace: if True: strip trailing and leading whitespace for results
    - extra_pipe: string containing other command(s) to pipe grepped output to
        - only applied when using pattern, not regex
    - show: if True, show the `grep` command before executing
        - only applied when using pattern, not regex

    Return list of strings (split on newline)
    """
    results = []
    if regex:
        if type(regex) != re.Pattern:
            if ignore_case:
                regex = re.compile(r'{}'.format(regex), re.IGNORECASE)
            else:
                regex = re.compile(r'{}'.format(regex))

        for line in re.split('\r?\n', output):
            match = regex.match(line)
            if match:
                groups = match.groups()
                if groups:
                    if len(groups) == 1:
                        results.append(groups[0])
                    else:
                        results.append(groups)
                else:
                    results.append(line)

        if strip_whitespace:
            results = [r.strip() for r in results]
        if results_as_string:
            results = join_result_string_on.join(results)
    else:
        if pattern:
            grep_args = _prep_common_grep_args(
                pattern=pattern,
                ignore_case=ignore_case,
                invert=invert,
                lines_before_match=lines_before_match,
                lines_after_match=lines_after_match
            )

            cmd = 'echo {} | grep {}'.format(repr(output), grep_args)
            if extra_pipe:
                cmd += ' | {}'.format(extra_pipe)
            new_output = bh.run_output(cmd, strip=strip_whitespace, show=show)
        else:
            if extra_pipe:
                cmd = 'echo {} | {}'.format(repr(output), extra_pipe)
                new_output = bh.run_output(cmd, strip=strip_whitespace, show=show)
            else:
                new_output = output

        if results_as_string:
            results = new_output
            if join_result_string_on != '\n':
                if strip_whitespace:
                    results = join_result_string_on.join(ih.splitlines_and_strip(results))
                else:
                    results = join_result_string_on.join(ih.splitlines(results))
            else:
                if strip_whitespace:
                    results = results.strip()
        else:
            if strip_whitespace:
                results = ih.splitlines_and_strip(new_output)
            else:
                results = ih.splitlines(new_output)

    return results


def grep_select_vim(path='', recursive=False, pattern=None, ignore_case=True,
                    invert=False, lines_before_match=None,
                    lines_after_match=None, exclude_files=None,
                    exclude_dirs=None, open_all_together=False, show=False):
    """Use grep to find files, then present a menu of results and line numbers

    - path: path to directory where the search should be started, if not using
      current working directory
    - recursive: if True, use `-R` to search all files at path
    - pattern: grep pattern string (extended `-E` style allowed)
    - regex: a compiled regular expression (from re.compile)
        - or a string that can be passed to re.compile
        - if match groups are used, the group matches will be returned
    - ignore_case: if True, ignore case (`grep -i` or re.IGNORECASE)
    - invert: if True, select non-matching items (`grep -v`)
        - only applied when using pattern, not regex
    - lines_before_match: number of context lines to show before match
        - only applied when using pattern, not regex
        - will not be used if `invert=True`
    - lines_after_match: number of context lines to show after match
        - only applied when using pattern, not regex
        - will not be used if `invert=True`
    - exclude_files: list of file names and patterns to exclude from searching
        - or string separated by any of , ; |
    - exclude_dirs: list of dir names and patterns to exclude from searching
        - or string separated by any of , ; |
    - open_all_together: if True, don't open each individual file to the line
      number, just open them all in the same vim session

    Any selections made will result in the file(s) being opened with vim to the
    particular line number. If multiple selections are made and
    open_all_together is False, each will be opened after the previous file is
    closed.
    """
    results = []
    path = path or getcwd()
    path = fh.abspath(path)
    grep_args = _prep_common_grep_args(
        pattern=pattern,
        ignore_case=ignore_case,
        invert=invert,
        lines_before_match=lines_before_match,
        lines_after_match=lines_after_match,
        exclude_files=exclude_files,
        exclude_dirs=exclude_dirs
    )
    grep_args += ' -n'
    if recursive:
        grep_args += ' -R .'
    else:
        files = [repr(f) for f in listdir('.') if isfile(f)]
        grep_args += ' ' + ' '.join(files)

    results = []
    rx1 = re.compile(r'^(?P<filename>[^:]+):(?P<line_no>\d+):(?P<line>.*)$')
    rx2 = re.compile(r'^(?P<filename>.+)-(?P<line_no>\d+)-(?P<line>.*)$')
    for line in ih.splitlines(bh.run_output('grep {}'.format(grep_args))):
        match1 = rx1.match(line)
        match2 = rx2.match(line)
        if match1:
            results.append(match1.groupdict())
        elif match2:
            results.append(match2.groupdict())

    prompt = "Select matches that you want to open to with vim"
    selected = ih.make_selections(
        results,
        prompt=prompt,
        wrap=False,
        item_format='{filename} ({line_no}) {line}'
    )

    if selected:
        if open_all_together:
            vim_args = ' '.join(sorted(set(repr(s['filename']) for s in selected)))
            bh.run('vim {}'.format(vim_args))
        else:
            for s in selected:
                bh.run('vim {} +{}'.format(repr(s['filename']), s['line_no']))
