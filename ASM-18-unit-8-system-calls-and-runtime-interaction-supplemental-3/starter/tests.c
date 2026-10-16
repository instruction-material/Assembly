#define _GNU_SOURCE
#include "lab.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    char directory[] = "/tmp/assembly-openat-contract-XXXXXX";
    if (!mkdtemp(directory)) return 1;
    int dirfd = -1, filefd = -1, result = 1;
    const mode_t old_mask = umask(077);
    dirfd = open(directory, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (dirfd < 0) goto cleanup;
    const unsigned int modes[] = {0400U, 0600U, 0700U};
    for (size_t i = 0; i < sizeof modes / sizeof modes[0]; ++i) {
        int preserved = 0;
        struct stat status;
        errno = 73;
        const long created = abi_probe(lab_openat, dirfd, "owned-note", O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, modes[i], &preserved);
        const int saved_errno = errno;
        if (created < 0 || created > 2147483647L) goto cleanup;
        filefd = (int)created;
        if (fstat(filefd, &status) != 0 || (unsigned int)(status.st_mode & 0777) != modes[i] || !preserved || saved_errno != 73) {
            fprintf(stderr, "openat contract requested=%04o preserved=%d errno=%d\n", modes[i], preserved, saved_errno);
            goto cleanup;
        }
        errno = 73;
        if (lab_openat(dirfd, "owned-note", O_WRONLY | O_CREAT | O_EXCL, modes[i]) != -EEXIST || errno != 73) goto cleanup;
        (void)close(filefd); filefd = -1;
        if (unlinkat(dirfd, "owned-note", 0) != 0) goto cleanup;
    }
    errno = 73;
    if (lab_openat(dirfd, "missing/note", O_RDONLY, 0) != -ENOENT || errno != 73) goto cleanup;
    errno = 73;
    if (lab_openat(-1, "owned-note", O_RDONLY, 0) != -EBADF || errno != 73) goto cleanup;
    puts("three actual creation modes; five raw errors; six preserved registers accepted");
    result = 0;
cleanup:
    if (filefd >= 0) (void)close(filefd);
    if (dirfd >= 0) { (void)unlinkat(dirfd, "owned-note", 0); (void)close(dirfd); }
    (void)umask(old_mask);
    if (rmdir(directory) != 0) result = 1;
    return result;
}
