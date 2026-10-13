#define _GNU_SOURCE
#include "array_routines.h"
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int preserved_sum_ok(const int32_t *, int64_t);
int preserved_search_ok(const int32_t *, int64_t, int32_t);
static unsigned cases;
static int check(const int32_t *values, int64_t count, int32_t threshold) {
    uint64_t bits = 0;
    int64_t expected_first = -1;
    int32_t before[64];
    if (count > 64) abort();
    for (int64_t i = 0; i < count; ++i) {
        before[i] = values[i];
        bits += (uint64_t)(int64_t)values[i];
        if (expected_first == -1 && values[i] >= threshold) expected_first = i;
    }
    int64_t expected_sum;
    memcpy(&expected_sum, &bits, sizeof(expected_sum));
    const int64_t actual_sum = asm_sum_array(values, count);
    const int64_t actual_first = asm_find_first_ge(values, count, threshold);
    if (actual_sum != expected_sum || actual_first != expected_first) {
        fprintf(stderr, "count=%" PRId64 " threshold=%" PRId32
                " expected=%" PRId64 ",%" PRId64 " actual=%" PRId64 ",%" PRId64 "\n",
                count, threshold, expected_sum, expected_first, actual_sum, actual_first);
        return 0;
    }
    if (count > 0 && memcmp(before, values, (size_t)count * sizeof(*values)) != 0) {
        fputs("input array changed\n", stderr);
        return 0;
    }
    if (!preserved_sum_ok(values, count) || !preserved_search_ok(values, count, threshold)) {
        fputs("callee-saved register contract failed\n", stderr);
        return 0;
    }
    ++cases;
    return 1;
}
static int guards(void) {
    const long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) return 0;
    const size_t page = (size_t)page_size;
    unsigned char *mapping = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                  MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) return 0;
    int32_t *values = (int32_t *)(mapping + page - 3 * sizeof(int32_t));
    values[0] = INT32_MIN; values[1] = -1; values[2] = INT32_MAX;
    if (mprotect(mapping + page, page, PROT_NONE) ||
        mprotect(mapping, page, PROT_READ)) {
        munmap(mapping, 2 * page);
        return 0;
    }
    int okay = check(values, 3, INT32_MAX) && check(values, 3, 0)
               && check(values, 3, INT32_MIN);
    if (munmap(mapping, 2 * page)) return 0;
    return okay;
}
int main(void) {
    _Static_assert(sizeof(int64_t) == sizeof(uint64_t), "64-bit bit pattern");
    if (!guards()) { fputs("guard-page contract failed\n", stderr); return 1; }
    const int32_t thresholds[] = {INT32_MIN, -100, -1, 0, 1, 100, INT32_MAX};
    for (size_t t = 0; t < sizeof(thresholds) / sizeof(thresholds[0]); ++t)
        if (!check(NULL, 0, thresholds[t]) || !check(NULL, -1, thresholds[t]) ||
            !check(NULL, INT64_MIN, thresholds[t])) return 1;
    const int32_t fixed[][7] = {
        {12, -4, 7, 19, 3, 19, -8},
        {INT32_MAX, INT32_MAX, INT32_MAX, 1, -1, 0, INT32_MIN},
        {INT32_MIN, INT32_MIN, INT32_MIN, -1, 1, 0, INT32_MAX},
        {-5, -5, -5, 7, 7, 7, -5},
        {0, 0, 0, 0, 0, 0, 0}
    };
    for (size_t f = 0; f < sizeof(fixed) / sizeof(fixed[0]); ++f)
        for (int64_t count = 0; count <= 7; ++count)
            for (size_t t = 0; t < sizeof(thresholds) / sizeof(thresholds[0]); ++t)
                if (!check(fixed[f], count, thresholds[t])) return 1;
    uint32_t state = UINT32_C(0x12345678);
    for (unsigned round = 0; round < 32; ++round) {
        int32_t values[48];
        for (size_t i = 0; i < 48; ++i) {
            state = state * UINT32_C(1664525) + UINT32_C(1013904223);
            memcpy(&values[i], &state, sizeof(state));
        }
        values[0] = INT32_MIN; values[23] = values[24]; values[47] = INT32_MAX;
        for (int64_t count = 0; count <= 48; ++count)
            for (size_t t = 0; t < sizeof(thresholds) / sizeof(thresholds[0]); ++t)
                if (!check(values, count, thresholds[t])) return 1;
    }
    printf("%u array cases accepted; bounded reads and unchanged input verified\n", cases);
    return 0;
}
