37d36
< ./history.tests: line 57: history: /newhistory: cannot create: Permission denied
39c38,39
< cat: /newhistory: No such file or directory
---
> echo line for history
> HISTFILE=$TMPDIR/newhistory
48c48,55
< cat: /newhistory: No such file or directory
---
> for i in one two three; do echo $i; done
> /bin/sh -c 'echo this is $0'
> ls
> echo $BASH_VERSION
> echo line for history
> HISTFILE=$TMPDIR/newhistory
> echo displaying \$HISTFILE after history -a
> cat $HISTFILE
183a191,195
> (left
> mid
> right)
> A
> B
185c197,201
< cat: /newhistory-1926697: No such file or directory
---
> (left
> mid
> right)
> A
> B
186a203,215
> 0
> 1
> 2
> (left
> mid
> right)
> A
> B
> (left
> mid
> right)
> A
> B
187a217,229
> 0
> 1
> 2
> (left
> mid
> right)
> A
> B
> (left
> mid
> right)
> A
> B
258d299
< rm: cannot remove '/newhistory': No such file or directory
