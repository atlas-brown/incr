/* Keep THIS_SH a real binary, preserve argv[0], and record invocation coverage. */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <unistd.h>

static void json_string(FILE *stream, const char *value) {
    fputc('"', stream);
    for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
        if (*p == '"' || *p == '\\') fprintf(stream, "\\%c", *p);
        else if (*p < 32 || *p >= 127) fprintf(stream, "\\u%04x", *p);
        else fputc(*p, stream);
    }
    fputc('"', stream);
}

int main(int argc, char **argv) {
    const char *target = STUDY_TARGET;
    const char *log = STUDY_LOG;
    FILE *stream = fopen(log, "a");
    if (!stream) { perror("invocation log"); return 125; }
    if (flock(fileno(stream), LOCK_EX)) return 125;
    fputs("{\"argv\":[", stream);
    for (int i = 0; i < argc; ++i) {
        if (i) fputc(',', stream);
        json_string(stream, argv[i]);
    }
    char *cwd = getcwd(NULL, 0);
    fputs("],\"cwd\":", stream);
    json_string(stream, cwd ? cwd : "");
    fputs("}\n", stream);
    free(cwd);
    fflush(stream);
    flock(fileno(stream), LOCK_UN);
    fclose(stream);
    char **args = calloc((size_t)argc + 2, sizeof(char *));
    if (!args) return 125;
    args[0] = argv[0];
    int j = 1;
    if (STUDY_OBSERVE) {
        if (setenv("INCR_ARGV0", argv[0], 1)) return 125;
        args[j++] = "-b";
    }
    for (int i = 1; i < argc; ++i) args[j++] = argv[i];
    execv(target, args);
    perror("execv");
    return 126;
}
