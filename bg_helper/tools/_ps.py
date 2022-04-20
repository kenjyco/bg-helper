__all__ = [
    'ps_output'
]

import re
import bg_helper as bh
import input_helper as ih
from input_helper.matcher import PsOutputMatcher


_ps_output_matcher = PsOutputMatcher()


def ps_output():
    """Return a list of dicts containing info about current running processes"""
    cmd = 'ps -eo user,pid,ppid,tty,command'
    output = bh.run_output(cmd)
    results = [
        _ps_output_matcher(line)
        for line in re.split('\r?\n', output)
    ]
    return results
