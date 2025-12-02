10,12c10,11
< bash: notthere: No such file or directory
< cp: cannot stat 'notthere': No such file or directory
< 0
---
> /tmp/bash: notthere: No such file or directory
> 127
25d23
< trap -- 'echo USR1' SIGUSR1
26a25
> trap -- 'echo USR1' SIGUSR1
31d29
< trap -- 'echo USR1' SIGUSR1
32a31
> trap -- 'echo USR1' SIGUSR1
35c34
< ./execscript: line 71: notthere: command not found
---
> ./execscript: line 71: notthere: No such file or directory
37c36
< ./execscript: line 74: notthere: command not found
---
> ./execscript: line 74: notthere: No such file or directory
43c42
< /home/vagozino/incr/venv/bin:/home/vagozino/.cargo/bin:/opt/orbstack-guest/bin-hiprio:/opt/orbstack-guest/data/bin/cmdlinks:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games:/opt/orbstack-guest/bin:/home/vagozino/incr/evaluation/bash-ts/bash
---
> unset
63,64d61
< mkdir: cannot create directory 'testa': File exists
< mkdir: cannot create directory 'testb': File exists
