3,4c3,4
< #2: pat=ab[/]cd/efg      yes/no
< #3: pat=ab[/a]cd/efg     yes/no
---
> #2: pat=ab[/]cd/efg      no/no
> #3: pat=ab[/a]cd/efg     no/no
6,7c6,7
< #5: pat=ab[!a]cd/efg     yes/no
< #6: pat=ab[.-0]cd/efg    yes/no
---
> #5: pat=ab[!a]cd/efg     no/no
> #6: pat=ab[.-0]cd/efg    no/no
25,27c25,27
< #22: pat=ab[/]ef              str=ab[/]ef          no/yes
< #23: pat=ab[/]ef              str=ab/ef            yes/no
< #24: pat=ab[c/d]ef            str=ab[c/d]ef        no/yes
---
> #22: pat=ab[/]ef              str=ab[/]ef          yes/yes
> #23: pat=ab[/]ef              str=ab/ef            no/no
> #24: pat=ab[c/d]ef            str=ab[c/d]ef        yes/yes
29,39c29,39
< #26: pat=ab[.-/]ef            str=ab[.-/]ef        no/yes
< #27: pat=ab[.-/]ef            str=ab.ef            yes/no
< #28: pat=ab[[=/=]]ef          str=ab[[=/=]]ef      no/yes
< #29: pat=ab[[=/=]]ef          str=ab/ef            yes/no
< #30: pat=ab[[=c=]/]ef         str=ab[=/]ef         no/yes
< #31: pat=ab[[=c=]/]ef         str=abcef            yes/no
< #32: pat=ab[[:alpha:]/]ef     str=ab[:/]ef         no/yes
< #33: pat=ab[[:alpha:]/]ef     str=abxef            yes/no
< #34: pat=ab[/[abc]]ef         str=ab[/c]ef         no/yes
< #35: pat=ab[/[abc]]ef         str=abc]ef           yes/no
< #36: pat=ab[c[=/=]]ef         str=ab[c[=/=]]ef     no/yes
---
> #26: pat=ab[.-/]ef            str=ab[.-/]ef        yes/yes
> #27: pat=ab[.-/]ef            str=ab.ef            no/no
> #28: pat=ab[[=/=]]ef          str=ab[[=/=]]ef      yes/yes
> #29: pat=ab[[=/=]]ef          str=ab/ef            no/no
> #30: pat=ab[[=c=]/]ef         str=ab[=/]ef         yes/yes
> #31: pat=ab[[=c=]/]ef         str=abcef            no/no
> #32: pat=ab[[:alpha:]/]ef     str=ab[:/]ef         yes/yes
> #33: pat=ab[[:alpha:]/]ef     str=abxef            no/no
> #34: pat=ab[/[abc]]ef         str=ab[/c]ef         yes/yes
> #35: pat=ab[/[abc]]ef         str=abc]ef           no/no
> #36: pat=ab[c[=/=]]ef         str=ab[c[=/=]]ef     yes/yes
41,44c41,44
< #38: pat=ab[c[=/=]]ef         str=abcef            yes/no
< #39: pat=a[b\/c]              str=a[b/c]           no/yes
< #40: pat=a[b\/c]              str=ab               yes/no
< #41: pat=a[b\/c]              str=ac               yes/no
---
> #38: pat=ab[c[=/=]]ef         str=abcef            no/no
> #39: pat=a[b\/c]              str=a[b/c]           yes/yes
> #40: pat=a[b\/c]              str=ab               no/no
> #41: pat=a[b\/c]              str=ac               no/no
55c55
< #50: pat=ab[c-                str=ab[c-            no/yes
---
> #50: pat=ab[c-                str=ab[c-            yes/yes
57c57
< #52: pat=ab[c\                str=ab[c\            no/yes
---
> #52: pat=ab[c\                str=ab[c\            yes/yes
59c59
< #54: pat=ab[[\                str=ab[[\            no/yes
---
> #54: pat=ab[[\                str=ab[[\            yes/yes
63c63
< #56: pat=@([[.].])A])         str=]                no/yes
---
> #56: pat=@([[.].])A])         str=]                yes/yes
65c65
< #58: pat=@([[.].])A])         str=AA])             yes/no
---
> #58: pat=@([[.].])A])         str=AA])             no/no
67,68c67,68
< #60: pat=@([[=]=])A])         str===]A])           no/yes
< #61: pat=@([[=]=])A])         str=AA])             yes/no
---
> #60: pat=@([[=]=])A])         str===]A])           yes/yes
> #61: pat=@([[=]=])A])         str=AA])             no/no
71c71
< #62: pat=[[=]=]ab]            str=a                yes/no
---
> #62: pat=[[=]=]ab]            str=a                no/no
76,77c76,77
< #66: pat=[a[.[=.]b]           str=a                no/yes
< #67: pat=[a[.[==].]b]         str=a                no/yes
---
> #66: pat=[a[.[=.]b]           str=a                yes/yes
> #67: pat=[a[.[==].]b]         str=a                yes/yes
79c79
< #68: pat=[a[=]=]b]            str=b                yes/no
---
> #68: pat=[a[=]=]b]            str=b                no/no
82c82
< #71: pat=[a[.[=.]b]           str=ab]              yes/no
---
> #71: pat=[a[.[=.]b]           str=ab]              no/no
84c84
< #73: pat=[a[.[==].]b]         str=ab]              yes/no
---
> #73: pat=[a[.[==].]b]         str=ab]              no/no
87c87
< #74: pat=x[a[:y]              str=x[               no/yes
---
> #74: pat=x[a[:y]              str=x[               yes/yes
92,95c92,95
< #78: pat=x[a[.y]              str=x[               no/yes
< #79: pat=x[a[.y]              str=x.               no/yes
< #80: pat=x[a[.y]              str=xy               no/yes
< #81: pat=x[a[.y]              str=x[ay             yes/no
---
> #78: pat=x[a[.y]              str=x[               yes/yes
> #79: pat=x[a[.y]              str=x.               yes/yes
> #80: pat=x[a[.y]              str=xy               yes/yes
> #81: pat=x[a[.y]              str=x[ay             no/no
