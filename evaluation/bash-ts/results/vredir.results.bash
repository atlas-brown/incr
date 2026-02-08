87,88c87,88
< ./vredir6.sub: line 10: /dev/null: Too many open files
< ./vredir6.sub: line 13: /dev/null: Too many open files
---
> ./vredir6.sub: redirection error: cannot duplicate fd: Invalid argument
> ./vredir6.sub: line 13: /dev/null: Invalid argument
