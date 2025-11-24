Testing /home/vagozino/incr/evaluation/bash-ts/bash/bash
version: 5.2.37(1)-release
HOSTTYPE = x86_64
OSTYPE = linux-gnu
MACHTYPE = x86_64-pc-linux-gnu
Testing /home/vagozino/incr/evaluation/bash-ts/bash/bash
Any output from any test, unless otherwise noted, indicates a possible anomaly
run-comsub-eof
6c6,7
< 
---
> ./comsub-eof3.sub: line 4: warning: here-document at line 1 delimited by end-of-file (wanted `EOF')
> ./comsub-eof3.sub: line 5: unexpected EOF while looking for matching `)'
run-comsub-posix
run-dollars
run-dynvar
run-execscript
8,14c8,11
< ./execscript: line 21: ./notthere: Permission denied
< 126
< Traceback (most recent call last):
<   File "/home/vagozino/incr/src/scripts/insert.py", line 3, in <module>
<     import libbash
< ModuleNotFoundError: No module named 'libbash'
< 0
---
> ./execscript: line 21: notthere: command not found
> 127
> /tmp/bash: notthere: No such file or directory
> 127
27d23
< trap -- 'echo USR1' SIGUSR1
28a25
> trap -- 'echo USR1' SIGUSR1
33d29
< trap -- 'echo USR1' SIGUSR1
34a31
> trap -- 'echo USR1' SIGUSR1
37,40c34,37
< ./execscript: line 71: notthere: Permission denied
< 126
< ./execscript: line 74: notthere: Permission denied
< 126
---
> ./execscript: line 71: notthere: No such file or directory
> 127
> ./execscript: line 74: notthere: No such file or directory
> 127
run-func
run-getopts
run-heredoc
122a123,129
> ./heredoc7.sub: line 17: warning: command substitution: 1 unterminated here-document
> foo bar
> ./heredoc7.sub: line 21: after: command not found
> ./heredoc7.sub: line 29: warning: here-document at line 29 delimited by end-of-file (wanted `EOF')
> ./heredoc7.sub: line 29: foobar: command not found
> ./heredoc7.sub: line 30: EOF: command not found
> grep: *.c: No such file or directory
run-ifs-posix
run-input-test
run-invert
run-iquote
run-more-exp
run-nquote
run-posix2
run-posixpat
run-posixpipe
run-precedence
run-quote
run-read
80c80
< 
---
> abcde
run-rhs-exp
run-strip
run-tilde
run-type
3,4c3
< notthere is ./notthere
< ./notthere
---
> ./type.tests: line 25: type: notthere: not found
