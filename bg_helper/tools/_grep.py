__all__ = [
    'grep_output'
]

import re
import bg_helper as bh
import input_helper as ih


def grep_output(output, pattern=None, regex=None, invert=False, extra_pipe=None):
    """Use grep to match lines of output against pattern

    - output: some output you would be piping to grep in a shell environment
    - pattern: grep pattern string
    - regex: a compiled regular expression (from re.compile)
        - or a sting that can be passed to re.compile
    - invert: if True, select non-matching items (`grep -v`)
        - only applied when using pattern, not regex
    - extra_pipe: string containing other command(s) to pipe grepped output to
        - only applied when using pattern, not regex

    Return list of strings (split on newline)
    """
    results = []
    if regex:
        if type(regex) != re.Pattern:
            regex = re.compile(r'{}'.format(regex))

        results = [
            line
            for line in re.split('\r?\n', output)
            if regex.match(line)
        ]
    else:
        if pattern:
            if invert:
                cmd = 'echo {} | grep -ivE {}'.format(repr(output), repr(pattern))
            else:
                cmd = 'echo {} | grep -iE {}'.format(repr(output), repr(pattern))
            if extra_pipe:
                cmd += ' | {}'.format(extra_pipe)
            new_output = bh.run_output(cmd)
        else:
            if extra_pipe:
                cmd = 'echo {} | {}'.format(repr(output), extra_pipe)
                new_output = bh.run_output(cmd)
            else:
                new_output = output

        results = ih.splitlines(new_output)

    return results
