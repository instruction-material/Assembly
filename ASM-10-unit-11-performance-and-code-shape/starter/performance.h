#ifndef PERFORMANCE_H
#define PERFORMANCE_H
#include <stddef.h>
#include <stdint.h>

uint64_t sum_nonnegative_branch(const int64_t *values, int64_t count);
uint64_t sum_nonnegative_cmov(const int64_t *values, int64_t count);
uint64_t sum_nonnegative_indexed(const int64_t *values,
                               const uint64_t *indices, int64_t count);
int preserved_branch_ok(const int64_t *values, int64_t count);
int preserved_cmov_ok(const int64_t *values, int64_t count);
int preserved_indexed_ok(const int64_t *values,
                         const uint64_t *indices, int64_t count);
uint64_t performance_reference(const int64_t *values, int64_t count);
void performance_dataset(int64_t *values, uint64_t *identity,
                         uint64_t *permutation, size_t count,
                         int pattern, uint64_t seed);
#endif
