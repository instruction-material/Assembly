#define _GNU_SOURCE
#include "lab.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed"))) {
        fputs("Use no argument or --changed.\n", stderr);
        return 64;
    }
    char directory[] = "/tmp/assembly-openat-XXXXXX";
    if (!mkdtemp(directory)) return 1;
    int dirfd = -1, filefd = -1, libcfd = -1, result = 1;
    const mode_t old_mask = umask(077);
    const unsigned int wanted_mode = argc == 2 ? 0400U : 0600U;
    struct stat status;
    dirfd = open(directory, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (dirfd < 0) goto cleanup;
    errno = 123;
    const long raw = lab_openat(dirfd, "owned-note", O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, wanted_mode);
    const int saved_errno = errno;
    if (raw < 0 || raw > 2147483647L) goto cleanup;
    filefd = (int)raw;
    if (fstat(filefd, &status) != 0) goto cleanup;
    const unsigned int actual_mode = (unsigned int)(status.st_mode & 0777);
    printf("raw-create mode=%04o requested=%04o errno=%d\n", actual_mode, wanted_mode, saved_errno);
    if (actual_mode != wanted_mode || saved_errno != 123) {
        fputs("Raw openat argument mapping unfinished or incorrect: complete SYSCALL_ARG4 and run the contracts.\n", stderr);
        result = 78;
        goto cleanup;
    }
    errno = 123;
    const long existing = lab_openat(dirfd, "owned-note", O_WRONLY | O_CREAT | O_EXCL, wanted_mode);
    const int existing_errno = errno;
    errno = 123;
    const long missing = lab_openat(dirfd, "missing/note", O_RDONLY | O_CLOEXEC, 0);
    const int missing_errno = errno;
    errno = 123;
    libcfd = openat(dirfd, "owned-note", O_WRONLY | O_CREAT | O_EXCL, wanted_mode);
    const int libc_errno = errno;
    if (existing != -EEXIST || existing_errno != 123 || missing != -ENOENT || missing_errno != 123 || libcfd != -1 || libc_errno != EEXIST) goto cleanup;
    printf("raw-existing=%ld raw-missing=%ld errno=%d libc-existing=%d libc-errno=%d\n", existing, missing, missing_errno, libcfd, libc_errno);
    result = 0;
cleanup:
    if (filefd >= 0) (void)close(filefd);
    if (libcfd >= 0) (void)close(libcfd);
    if (dirfd >= 0) { (void)unlinkat(dirfd, "owned-note", 0); (void)close(dirfd); }
    (void)umask(old_mask);
    if (rmdir(directory) != 0) result = 1;
    return result;
}
