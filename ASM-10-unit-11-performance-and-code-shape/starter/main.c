#define _POSIX_C_SOURCE 200809L
#include "performance.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static volatile uint64_t observed_checksum;

static uint64_t evaluate(int variant, const int64_t *values,
                         const uint64_t *identity,
                         const uint64_t *permutation, int64_t count) {
    switch (variant) {
        case 0: return sum_nonnegative_branch(values, count);
        case 1: return sum_nonnegative_cmov(values, count);
        case 2: return sum_nonnegative_indexed(values, identity, count);
        default: return sum_nonnegative_indexed(values, permutation, count);
    }
}

static int parse_bound(const char *text, uint64_t low,
                       uint64_t high, uint64_t *result) {
    if (!*text) return 0;
    for (const char *p = text; *p; ++p) {
        if (*p < '0' || *p > '9') return 0;
    }
    errno = 0;
    char *end = NULL;
    unsigned long long value = strtoull(text, &end, 10);
    if (errno || !end || *end || value < low || value > high) return 0;
    *result = (uint64_t)value;
    return 1;
}

static int example(void) {
    const int64_t values[] = {-3, 0, 5, INT64_MAX, INT64_MAX};
    const uint64_t order[] = {4, 1, 0, 3, 2};
    const uint64_t branch = sum_nonnegative_branch(values, 5);
    const uint64_t cmov = sum_nonnegative_cmov(values, 5);
    const uint64_t indexed = sum_nonnegative_indexed(values, order, 5);
    printf("branch=%" PRIu64 " cmov=%" PRIu64 " indexed=%" PRIu64
           " expected=3\n", branch, cmov, indexed);
    return (branch == 3 && cmov == 3 && indexed == 3) ? 0 : 1;
}

static int elapsed(const struct timespec *start, const struct timespec *end,
                   uint64_t *result) {
    if (end->tv_sec < start->tv_sec ||
        (end->tv_sec == start->tv_sec && end->tv_nsec < start->tv_nsec)) {
        return 0;
    }
    uint64_t seconds = (uint64_t)end->tv_sec - (uint64_t)start->tv_sec;
    int64_t nanos = (int64_t)end->tv_nsec - (int64_t)start->tv_nsec;
    if (nanos < 0) { --seconds; nanos += INT64_C(1000000000); }
    *result = seconds * UINT64_C(1000000000) + (uint64_t)nanos;
    return 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--example") == 0) return example();
    uint64_t count = 4096, repeats = 32, trials = 5;
    if ((argc != 1 && argc != 2 && argc != 5) ||
        (argc >= 2 && strcmp(argv[1], "--benchmark") != 0) ||
        (argc == 5 && (!parse_bound(argv[2], 64, 1048576, &count) ||
         !parse_bound(argv[3], 1, 1024, &repeats) ||
         !parse_bound(argv[4], 1, 21, &trials))) ||
        (count & (count - 1)) != 0 ||
        count * repeats * trials * UINT64_C(12) > UINT64_C(2000000000)) {
        fputs("usage: assembly_performance [--example | --benchmark "
              "[power_of_two_count repeats trials]]\n", stderr);
        return 2;
    }
    int64_t *values = malloc((size_t)count * sizeof *values);
    uint64_t *identity = malloc((size_t)count * sizeof *identity);
    uint64_t *permutation = malloc((size_t)count * sizeof *permutation);
    if (!values || !identity || !permutation) {
        free(values); free(identity); free(permutation);
        fputs("allocation failed\n", stderr);
        return 2;
    }
    const char *patterns[] = {"nonnegative", "alternating", "seeded-mixed"};
    const char *variants[] = {"branch-sequential", "cmov-sequential",
                             "indexed-identity", "indexed-permuted"};
    int status = 0;
    puts("pattern,variant,trial,count,repeats,elapsed_ns,checksum,"
         "expected_checksum,seed");
    for (int pattern = 0; pattern < 3 && status == 0; ++pattern) {
        uint64_t seed = UINT64_C(0x814fa27065b39c12) + (uint64_t)pattern;
        performance_dataset(values, identity, permutation, (size_t)count,
                            pattern, seed);
        uint64_t expected = performance_reference(values, (int64_t)count);
        for (int variant = 0; variant < 4; ++variant) {
            if (evaluate(variant, values, identity, permutation,
                         (int64_t)count) != expected) status = 1;
            observed_checksum = evaluate(variant, values, identity,
                                         permutation, (int64_t)count);
        }
        if (status) break;
        for (uint64_t trial = 0; trial < trials && status == 0; ++trial) {
            for (int offset = 0; offset < 4; ++offset) {
                int variant = (int)((trial + (uint64_t)offset) % UINT64_C(4));
                struct timespec start, end;
                uint64_t checksum = 0, nanoseconds = 0;
                if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
                    status = 2; break;
                }
                for (uint64_t repeat = 0; repeat < repeats; ++repeat) {
                    checksum += evaluate(variant, values, identity,
                                          permutation, (int64_t)count);
                }
                if (clock_gettime(CLOCK_MONOTONIC, &end) != 0 ||
                    !elapsed(&start, &end, &nanoseconds)) {
                    status = 2; break;
                }
                observed_checksum = checksum;
                if (checksum != expected * repeats) { status = 1; break; }
                printf("%s,%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
                       ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 "\n",
                       patterns[pattern], variants[variant], trial, count,
                       repeats, nanoseconds, checksum, expected * repeats, seed);
            }
        }
    }
    free(values); free(identity); free(permutation);
    if (status) fputs(status == 1 ? "correctness check failed\n" :
                     "monotonic clock failed\n", stderr);
    return status;
}
