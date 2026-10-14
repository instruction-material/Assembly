#define _GNU_SOURCE
#include "performance.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static int check(const int64_t *values, const uint64_t *indices, int64_t count,
                 uint64_t expected, uint64_t expected_indexed) {
    uint64_t branch = sum_nonnegative_branch(values, count);
    uint64_t cmov = sum_nonnegative_cmov(values, count);
    uint64_t indexed = sum_nonnegative_indexed(values, indices, count);
    if (branch != expected || cmov != expected || indexed != expected_indexed) {
        fprintf(stderr, "sum mismatch: branch=%" PRIu64 " cmov=%" PRIu64
                " indexed=%" PRIu64 " expected=%" PRIu64 "/%" PRIu64 "\n",
                branch, cmov, indexed, expected, expected_indexed);
        return 0;
    }
    if (!preserved_branch_ok(values, count) ||
        !preserved_cmov_ok(values, count) ||
        !preserved_indexed_ok(values, indices, count)) {
        fputs("preserved register mismatch\n", stderr); return 0;
    }
    return 1;
}

static int oracle(void) {
    int64_t count;
    unsigned cases = 0;
    int scanned;
    while ((scanned = scanf("%" SCNd64, &count)) == 1) {
        if (count > 64) return 2;
        int64_t values[64];
        uint64_t indices[64], expected, expected_indexed;
        for (int64_t i = 0; i < count; ++i) {
            if (scanf("%" SCNd64, &values[i]) != 1) return 2;
        }
        for (int64_t i = 0; i < count; ++i) {
            if (scanf("%" SCNu64, &indices[i]) != 1 ||
                indices[i] >= (uint64_t)count) return 2;
        }
        if (scanf("%" SCNu64 " %" SCNu64, &expected, &expected_indexed) != 2) return 2;
        if (!check(count > 0 ? values : NULL, count > 0 ? indices : NULL,
                   count, expected, expected_indexed)) return 1;
        ++cases;
    }
    if (scanned != EOF || !cases) return 2;
    printf("performance oracle cases passed: %u\n", cases);
    return 0;
}

static int physical(void) {
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) return 0;
    size_t page = (size_t)page_size;
    void *data_map = mmap(NULL, page * 3, PROT_NONE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    void *index_map = mmap(NULL, page * 3, PROT_NONE,
                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (data_map == MAP_FAILED || index_map == MAP_FAILED) {
        if (data_map != MAP_FAILED) munmap(data_map, page * 3);
        if (index_map != MAP_FAILED) munmap(index_map, page * 3);
        return 0;
    }
    unsigned char *data = (unsigned char *)data_map + page;
    unsigned char *index = (unsigned char *)index_map + page;
    int ok = mprotect(data, page, PROT_READ | PROT_WRITE) == 0 &&
             mprotect(index, page, PROT_READ | PROT_WRITE) == 0;
    int64_t *end_values = (int64_t *)(data + page - 3 * sizeof(int64_t));
    uint64_t *end_indices = (uint64_t *)(index + page - 3 * sizeof(uint64_t));
    const int64_t end_case[] = {-1, INT64_MAX, INT64_MAX};
    const uint64_t order[] = {2, 0, 1};
    const int64_t start_case[] = {-3, 0, 5};
    const uint64_t repeats[] = {2, 2, 2};
    if (ok) {
        memcpy(end_values, end_case, sizeof end_case);
        memcpy(end_indices, order, sizeof order);
        memcpy(data, start_case, sizeof start_case);
        memcpy(index, repeats, sizeof repeats);
        ok = mprotect(data, page, PROT_READ) == 0 &&
             mprotect(index, page, PROT_READ) == 0;
    }
    if (ok) ok = check(end_values, end_indices, 3, UINT64_MAX - 1, UINT64_MAX - 1);
    if (ok) ok = check((const int64_t *)data, end_indices, 3, 5, 5);
    if (ok) ok = check((const int64_t *)data, (const uint64_t *)index, 3, 5, 15);
    if (ok) ok = check((const int64_t *)data_map, (const uint64_t *)index_map,
                       INT64_MIN, 0, 0);
    if (ok) ok = check((const int64_t *)data_map, (const uint64_t *)index_map, 0, 0, 0);
    int data_clean = munmap(data_map, page * 3) == 0;
    int index_clean = munmap(index_map, page * 3) == 0;
    return ok && data_clean && index_clean;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--oracle") == 0) return oracle();
    if (argc != 1) return 2;
    const int64_t values[] = {-3, 0, 5, INT64_MAX, INT64_MAX};
    const uint64_t order[] = {4, 1, 0, 3, 2};
    const int64_t wide[] = {INT64_C(4294967296), -1, INT64_MAX};
    const uint64_t wide_order[] = {2, 0, 0};
    const uint64_t repeated = (uint64_t)INT64_MAX + UINT64_C(8589934592);
    if (!check(values, order, 5, 3, 3) ||
        !check(wide, wide_order, 3, (uint64_t)INT64_MAX + UINT64_C(4294967296), repeated) ||
        !check(NULL, NULL, 0, 0, 0) ||
        !check(NULL, NULL, -1, 0, 0) ||
        !check(NULL, NULL, -2, 0, 0) ||
        !check(NULL, NULL, INT64_MIN, 0, 0) ||
        !physical()) return 1;
    puts("performance physical and fixed cases passed: 11");
    return 0;
}
