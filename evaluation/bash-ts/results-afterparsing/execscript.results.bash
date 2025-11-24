10,15c10,11
< Traceback (most recent call last):
<   File "/home/vagozino/incr/src/scripts/insert.py", line 3, in <module>
<     import libbash
< ModuleNotFoundError: No module named 'libbash'
< cp: cannot stat 'notthere': No such file or directory
< 0
---
> /tmp/bash: notthere: No such file or directory
> 127
28d23
< trap -- 'echo USR1' SIGUSR1
29a25
> trap -- 'echo USR1' SIGUSR1
34d29
< trap -- 'echo USR1' SIGUSR1
35a31
> trap -- 'echo USR1' SIGUSR1
38,41c34,37
< ./execscript: line 71: notthere: Permission denied
< 126
< ./execscript: line 74: notthere: Permission denied
< 126
---
> ./execscript: line 71: notthere: No such file or directory
> 127
> ./execscript: line 74: notthere: No such file or directory
> 127
