/* GNU time's -o stream is inherited by children. Strip instrumentation handles
 * before executing the top-level shell; its own intentional descriptors are
 * created later. Incr otherwise correctly declines caching inherited state. */
#define _GNU_SOURCE
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (syscall(SYS_close_range, 3U, UINT_MAX, 0U) != 0) {
        if (errno != ENOSYS) { perror("close_range"); return 125; }
        struct rlimit limit;
        if (getrlimit(RLIMIT_NOFILE, &limit) != 0) return 125;
        rlim_t end = limit.rlim_cur == RLIM_INFINITY ? 1048576 : limit.rlim_cur;
        for (rlim_t fd = 3; fd < end; fd++) close((int)fd);
    }
    execvp(argv[1], &argv[1]);
    int error = errno;
    perror(argv[1]);
    return error == ENOENT ? 127 : 126;
}
