#define _GNU_SOURCE
#include "debug_lab.h"
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static size_t cases;
static int check_case(const int32_t *values, int64_t count, int64_t expected) {
    int32_t before[64];
    if (count > 64) return 1;
    if (count > 0) memcpy(before, values, (size_t)count * sizeof(values[0]));
    if (!preserved_debug_ok(values, count)) {
        fputs("callee-saved register contract failed\n", stderr);
        return 1;
    }
    const int64_t observed = debug_first_nonnegative(values, count);
    if (observed != expected) {
        fprintf(stderr, "debug index mismatch: observed=%" PRId64 " expected=%" PRId64 "\n", observed, expected);
        return 1;
    }
    if (count > 0 && memcmp(before, values, (size_t)count * sizeof(values[0])) != 0) {
        fputs("source values changed\n", stderr);
        return 1;
    }
    cases++;
    return 0;
}
static int64_t expected_index(const int32_t *values, int64_t count) {
    for (int64_t i = 0; i < count; i++) if (values[i] >= 0) return i;
    return -1;
}
static uint64_t state = UINT64_C(0x6c38e715ac0294bf);
static uint64_t next_bits(void) {
    state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
    return state;
}
static int32_t next_value(void) {
    uint32_t bits = (uint32_t)(next_bits() >> 32);
    int32_t value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}
static int fixed_cases(void) {
    static const int32_t values[][3] = {
        {-8,-1,4}, {-8,0,4}, {0,0,0}, {-1,0,0},
        {INT32_MIN,0,0}, {INT32_MAX,0,0}, {INT32_MIN,-1,INT32_MAX},
        {-1,-2,-3}, {-1,1,1}, {1,-1,0}, {65535,-1,0}
    };
    static const int64_t lengths[] = {3,3,1,1,1,1,3,3,3,2,1};
    if (check_case(NULL,0,-1)) return 1;
    for (size_t i = 0; i < sizeof(lengths)/sizeof(lengths[0]); i++) {
        if (check_case(values[i], lengths[i], expected_index(values[i],lengths[i]))) return 1;
    }
    for (size_t sample = 0; sample < 10000; sample++) {
        int32_t row[64] = {0};
        int64_t count = (int64_t)(next_bits() % 65);
        for (int64_t i = 0; i < count; i++) row[i] = next_value();
        if (check_case(count ? row : NULL, count, expected_index(row,count))) return 1;
    }
    if (check_case(NULL,-1,-1) || check_case(NULL,-2,-1) || check_case(NULL,INT64_MIN,-1)) return 1;
    return 0;
}
static int oracle_cases(void) {
    int64_t count, expected;
    while (scanf("%" SCNd64, &count) == 1) {
        int32_t values[64];
        if (count > 64) return 1;
        for (int64_t i = 0; i < count; i++) if (scanf("%" SCNd32, &values[i]) != 1) return 1;
        if (scanf("%" SCNd64, &expected) != 1) return 1;
        if (check_case(count > 0 ? values : NULL, count, expected)) return 1;
    }
    return cases == 10015 ? 0 : 1;
}
static int guarded_cases(void) {
    long size = sysconf(_SC_PAGESIZE);
    if (size <= 0) return 1;
    size_t page = (size_t)size;
    unsigned char *memory = mmap(NULL, page * 2, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (memory == MAP_FAILED) return 1;
    int32_t *values = (int32_t *)(memory + page - 3 * sizeof(int32_t));
    values[0] = -8; values[1] = -1; values[2] = 4;
    int failed = mprotect(memory + page,page,PROT_NONE) != 0
        || mprotect(memory,page,PROT_READ) != 0
        || check_case(values,3,2);
    if (!failed) {
        failed = mprotect(memory,page,PROT_READ | PROT_WRITE) != 0;
        if (!failed) {
            values[2] = -7;
            failed = mprotect(memory,page,PROT_READ) != 0 || check_case(values,3,-1);
        }
    }
    if (!failed) failed = check_case((const int32_t *)(memory+page),0,-1)
        || check_case((const int32_t *)(memory+page),INT64_MIN,-1);
    if (munmap(memory,page*2) != 0) failed = 1;
    return failed;
}
int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1],"--oracle") != 0)) return 2;
    if ((argc == 2 ? oracle_cases() : fixed_cases()) || guarded_cases()) return 1;
    if (cases != 10019) return 1;
    printf("debug cases passed: %zu\n", cases);
    return 0;
}
