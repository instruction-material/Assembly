#define _GNU_SOURCE
#include "helper.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int preserved_helper_ok(const int32_t *, int64_t, int64_t, int64_t, int64_t);
uint64_t helper_call_count, helper_stack_mod;
int64_t helper_value, helper_min, helper_max;
static unsigned cases;
static int check(const int32_t *values, int64_t count, int64_t scale,
                 int64_t low, int64_t high) {
    if (count > 64 || low > high) abort();
    uint64_t bits = 0;
    int32_t before[64];
    for (int64_t i = 0; i < count; ++i) {
        before[i] = values[i];
        bits += (uint64_t)(int64_t)values[i];
    }
    bits *= (uint64_t)scale;
    int64_t scaled;
    memcpy(&scaled, &bits, sizeof(scaled));
    const int64_t expected = scaled < low ? low : scaled > high ? high : scaled;
    helper_call_count = 0;
    const int64_t actual = asm_scaled_clamped_sum(values, count, scale, low, high);
    if (helper_call_count != 1 || helper_value != scaled ||
        helper_min != low || helper_max != high) {
        fputs("helper invocation or argument contract failed\n", stderr);
        return 0;
    }
    if (helper_stack_mod != 8) {
        fputs("helper entry stack alignment contract failed\n", stderr);
        return 0;
    }
    if (actual != expected) {
        fprintf(stderr, "expected=%" PRId64 " actual=%" PRId64 "\n", expected, actual);
        return 0;
    }
    if (!preserved_helper_ok(values, count, scale, low, high)) {
        fputs("callee-saved register contract failed\n", stderr);
        return 0;
    }
    if (helper_call_count != 2 || helper_stack_mod != 8 ||
        helper_value != scaled || helper_min != low || helper_max != high) {
        fputs("repeated helper invocation contract failed\n", stderr);
        return 0;
    }
    if (count > 0 && memcmp(before, values, (size_t)count * sizeof(*values))) {
        fputs("input array changed\n", stderr);
        return 0;
    }
    ++cases;
    return 1;
}
static int guards(void) {
    const long size = sysconf(_SC_PAGESIZE);
    if (size <= 0) return 0;
    const size_t page = (size_t)size;
    unsigned char *mapping = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                  MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) return 0;
    int32_t *values = (int32_t *)(mapping + page - 5 * sizeof(int32_t));
    const int32_t original[] = {4, -2, 9, 6, -1};
    memcpy(values, original, sizeof(original));
    if (mprotect(mapping + page, page, PROT_NONE) ||
        mprotect(mapping, page, PROT_READ)) { munmap(mapping, 2 * page); return 0; }
    const int okay = check(values, 5, 3, -20, 40) &&
                     check(values, 5, -3, -40, 20) &&
                     check(values, 5, INT64_MAX, INT64_MIN, INT64_MAX);
    const int cleanup = munmap(mapping, 2 * page);
    return okay && !cleanup;
}
static int exercise(const int32_t *values, int64_t count) {
    const int64_t scales[] = {-3, -1, 0, 1, 3, 10, INT64_MIN, INT64_MAX, INT64_C(4294967297)};
    const int64_t bounds[][2] = {
        {-20, 40}, {-20, 25}, {-5, -1}, {1, 5}, {0, 0},
        {INT64_MIN, INT64_MAX}, {INT64_MAX, INT64_MAX}
    };
    for (size_t s = 0; s < 9; ++s)
        for (size_t b = 0; b < 7; ++b)
            if (!check(values, count, scales[s], bounds[b][0], bounds[b][1])) return 0;
    return 1;
}
int main(void) {
    _Static_assert(sizeof(int64_t) == sizeof(uint64_t), "64-bit bit pattern");
    if (!guards() || !exercise(NULL, 0) || !exercise(NULL, -1) ||
        !exercise(NULL, INT64_MIN)) return 1;
    const int32_t fixed[][7] = {
        {4, -2, 9, 6, -1, 0, 0},
        {INT32_MAX, INT32_MAX, INT32_MAX, 1, -1, 0, INT32_MIN},
        {INT32_MIN, INT32_MIN, INT32_MIN, -1, 1, 0, INT32_MAX},
        {-5, -5, -5, 7, 7, 7, -5},
        {0, 0, 0, 0, 0, 0, 0}
    };
    for (size_t f = 0; f < 5; ++f)
        for (int64_t count = 0; count <= 7; ++count)
            if (!exercise(fixed[f], count)) return 1;
    uint32_t state = UINT32_C(0x87654321);
    for (unsigned round = 0; round < 8; ++round) {
        int32_t values[16];
        for (size_t i = 0; i < 16; ++i) {
            state = state * UINT32_C(1664525) + UINT32_C(1013904223);
            memcpy(&values[i], &state, sizeof(state));
        }
        for (int64_t count = 0; count <= 16; ++count)
            if (!exercise(values, count)) return 1;
    }
    printf("%u helper cases accepted; call arguments and stack alignment verified\n", cases);
    return 0;
}
