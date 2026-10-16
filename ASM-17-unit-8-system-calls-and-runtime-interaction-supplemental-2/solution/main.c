#define _GNU_SOURCE
#include "lab.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void close_pair(int pair[2]) {
    for (int i = 0; i < 2; ++i) if (pair[i] >= 0) { (void)close(pair[i]); pair[i] = -1; }
}

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed"))) {
        fputs("Use no argument or --changed.\n", stderr);
        return 64;
    }
    const char *payload = argc == 2 ? "changed-kernel-bytes" : "owned-kernel-bytes";
    const size_t length = strlen(payload);
    unsigned char small[64] = {0};
    int pair[2] = {-1, -1};
    unsigned char *bytes = NULL, *observed = NULL;
    int result = 1;
    if (pipe2(pair, O_CLOEXEC) != 0) goto cleanup;
    errno = 123;
    const long sent = lab_write(pair[1], payload, length);
    const int raw_errno = errno;
    if (sent != (long)length || raw_errno != 123) {
        fputs("Raw write unfinished or incorrect: complete SYSCALL_WRITE and run the contracts.\n", stderr);
        result = 78;
        goto cleanup;
    }
    const ssize_t received = read(pair[0], small, length);
    if (received != (ssize_t)length || memcmp(small, payload, length)) goto cleanup;
    printf("raw bytes=%ld errno=%d payload=%s\n", sent, raw_errno, payload);
    errno = 123;
    const long raw_bad = lab_write(-1, payload, length);
    const int raw_bad_errno = errno;
    errno = 123;
    const ssize_t libc_bad = write(-1, payload, length);
    const int libc_bad_errno = errno;
    if (raw_bad != -EBADF || raw_bad_errno != 123 || libc_bad != -1 || libc_bad_errno != EBADF) goto cleanup;
    printf("raw-error result=%ld errno=%d libc-error result=%ld errno=%d\n", raw_bad, raw_bad_errno, (long)libc_bad, libc_bad_errno);
    close_pair(pair);
    if (pipe2(pair, O_CLOEXEC | O_NONBLOCK) != 0) goto cleanup;
    const int capacity = fcntl(pair[1], F_GETPIPE_SZ);
    if (capacity < 4096 || capacity > 65536) {
        fputs("This bounded lab requires an owned pipe capacity from 4096 through 65536 bytes.\n", stderr);
        result = 64;
        goto cleanup;
    }
    const size_t count = (size_t)capacity * 2;
    bytes = malloc(count);
    observed = malloc(count);
    if (!bytes || !observed) goto cleanup;
    for (size_t i = 0; i < count; ++i) bytes[i] = (unsigned char)(i * 37 + i / 251);
    errno = 123;
    const long first = lab_write(pair[1], bytes, count);
    const int first_errno = errno;
    const long full = lab_write(pair[1], bytes + (size_t)capacity, 1);
    const int full_errno = errno;
    if (first != capacity || first_errno != 123 || full != -EAGAIN || full_errno != 123) goto cleanup;
    const ssize_t got_first = read(pair[0], observed, (size_t)capacity);
    if (got_first != capacity || memcmp(observed, bytes, (size_t)capacity)) goto cleanup;
    const size_t remaining = count - (size_t)first;
    const long second = lab_write(pair[1], bytes + first, remaining);
    if (second != (long)remaining) goto cleanup;
    const ssize_t got_second = read(pair[0], observed + first, remaining);
    if (got_second != (ssize_t)remaining || memcmp(observed, bytes, count)) goto cleanup;
    printf("short-write requested=%zu first=%ld full=%ld remaining=%zu total=%ld bytes-checked=%zu\n", count, first, full, remaining, first + second, count);
    result = 0;
cleanup:
    close_pair(pair);
    free(bytes);
    free(observed);
    return result;
}
