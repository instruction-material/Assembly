#define _GNU_SOURCE
#include "hardening.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static uint64_t polynomial(const uint8_t *input, int64_t count) {
    if (count <= 0 || count > 32) return 0;
    uint64_t power = 1;
    uint64_t result = 0;
    for (int64_t i = count; i > 0; --i) {
        result += (uint64_t)input[i-1] * power;
        power *= UINT64_C(33);
    }
    return result + UINT64_C(5381) * power;
}
static int check(const uint8_t *input, int64_t count, uint64_t expected) {
    if (checksum_c(input, count) != expected ||
        checksum_asm(input, count) != expected ||
        !preserved_c_ok(input, count) || !preserved_asm_ok(input, count)) {
        fprintf(stderr, "checksum contract mismatch: count=%" PRId64 " expected=%" PRIu64 "\n", count, expected);
        return 0;
    }
    return 1;
}
int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--oracle") == 0) {
        int64_t count;
        uint64_t expected;
        unsigned cases = 0;
        while (scanf("%" SCNd64 " %" SCNu64, &count, &expected) == 2) {
            uint8_t values[32] = {0};
            for (int64_t i = 0; i < count && count <= 32; ++i) {
                unsigned value;
                if (scanf("%u", &value) != 1 || value > 255) return 2;
                values[i] = (uint8_t)value;
            }
            if (!check(count <= 0 || count > 32 ? NULL : values, count, expected)) return 1;
            ++cases;
        }
        if (!feof(stdin)) return 2;
        printf("hardening oracle cases passed: %u\n", cases);
        return 0;
    }
    if (argc != 1) return 2;
    const int64_t invalid[] = {0, -1, INT64_MIN, 33, INT64_MAX};
    unsigned cases = 0;
    for (size_t i = 0; i < sizeof invalid / sizeof invalid[0]; ++i) {
        if (!check(NULL, invalid[i], 0)) return 1;
        ++cases;
    }
    uint8_t values[32], before[32];
    for (size_t i = 0; i < sizeof values; ++i) values[i] = (uint8_t)(17U * i);
    memcpy(before, values, sizeof values);
    for (int64_t count = 1; count <= 32; ++count) {
        if (!check(values, count, polynomial(values, count))) return 1;
        ++cases;
    }
    if (memcmp(before, values, sizeof values) != 0) return 1;
    const long page = sysconf(_SC_PAGESIZE);
    if (page < 32) return 2;
    const size_t span = (size_t)page;
    uint8_t *memory = mmap(NULL, span * 3, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (memory == MAP_FAILED) return 2;
    for (int64_t count = 1; count <= 32; ++count) {
        if (mprotect(memory + span, span, PROT_READ | PROT_WRITE) != 0) return 2;
        uint8_t *input = memory + span * 2 - (size_t)count;
        for (int64_t i = 0; i < count; ++i) input[i] = (uint8_t)(255 - i);
        const uint64_t expected = polynomial(input, count);
        if (mprotect(memory + span, span, PROT_READ) != 0) return 2;
        if (!check(input, count, expected)) return 1;
        ++cases;
    }
    if (munmap(memory, span * 3) != 0) return 2;
    printf("hardening physical and fixed cases passed: %u\n", cases);
    return 0;
}
