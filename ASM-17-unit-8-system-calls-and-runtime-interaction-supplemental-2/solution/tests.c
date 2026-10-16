#define _GNU_SOURCE
#include "lab.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(void) {
    int pair[2] = {-1, -1};
    unsigned char bytes[65], observed[65];
    if (pipe2(pair, O_CLOEXEC) != 0) return 1;
    int result = 1;
    for (size_t i = 0; i < sizeof bytes; ++i) bytes[i] = (unsigned char)(255 - i * 3);
    for (size_t count = 1; count <= sizeof bytes; ++count) {
        int preserved = 0;
        errno = 73;
        const long sent = abi_probe(lab_write, pair[1], bytes, count, &preserved);
        const int saved_errno = errno;
        if (sent != (long)count || !preserved || saved_errno != 73) {
            fprintf(stderr, "write contract count=%zu observed=%ld preserved=%d errno=%d\n", count, sent, preserved, saved_errno);
            goto cleanup;
        }
        if (read(pair[0], observed, count) != (ssize_t)count || memcmp(observed, bytes, count)) goto cleanup;
    }
    errno = 73;
    const long bad = lab_write(-1, bytes, sizeof bytes);
    const int saved_errno = errno;
    if (bad != -EBADF || saved_errno != 73) goto cleanup;
    errno = 73;
    if (lab_write(pair[0], bytes, sizeof bytes) != -EBADF || errno != 73) goto cleanup;
    puts("65 byte-exact write cases; two raw EBADF cases; six preserved registers accepted");
    result = 0;
cleanup:
    (void)close(pair[0]);
    (void)close(pair[1]);
    return result;
}
