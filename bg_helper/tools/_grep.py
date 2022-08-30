__all__ = [
    'grep_output'
]

import re
import bg_helper as bh
import input_helper as ih


def grep_output(output, pattern=None, regex=None, ignore_case=True, invert=False,
                lines_before_match=None, lines_after_match=None,
                results_as_string=False, join_result_string_on='\n',
                strip_whitespace=False, extra_pipe=None, show=False):
    """Use grep to match lines of output against pattern

    - output: some output you would be piping to grep in a shell environment
    - pattern: grep pattern string (extended `-E` style allowed)
    - regex: a compiled regular expression (from re.compile)
        - or a sting that can be passed to re.compile
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
            _grep_args = '-'
            if ignore_case:
                _grep_args += 'i'
            if invert:
                _grep_args += 'v'
            else:
                if _grep_args == '-':
                    _grep_args = ''
                if lines_before_match:
                    _grep_args = '-B {} '.format(lines_before_match) + _grep_args
                if lines_after_match:
                    _grep_args = '-A {} '.format(lines_after_match) + _grep_args
            if '(' in pattern and '|' in pattern and ')' in pattern:
                _grep_args += ' -E {}'.format(repr(pattern))
            else:
                _grep_args += ' {}'.format(repr(pattern))

            cmd = 'echo {} | grep {}'.format(repr(output), _grep_args)
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
