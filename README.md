## Install

```
% pip3 install bg-helper
```

## Usage

Use `bg_helper.call_func` when you need to call a function (with arbitrary
`*args` and `**kwargs`) and log any uncaught exceptions. A dict is returned with

- `func_name`
- `args`
- `kwargs`
- `status` (ok/error)

If the function call was successful, there will also be a `value` key. If there
was an uncaught exception, the following additional keys will be provided in the
return dict

- `error_type`
- `error_value`
- `fqdn`
- `func_doc`
- `func_module`
- `time_epoch`
- `time_string`
- `traceback_string`

Use `bg_helper.SimpleBackgroundTask` when you need to start a long-running
Python function, or system command (like `vlc` media player) in the background.

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
