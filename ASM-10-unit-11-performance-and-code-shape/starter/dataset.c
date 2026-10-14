#include "performance.h"
#include <string.h>

static uint64_t advance(uint64_t *state) {
    *state = *state * UINT64_C(6364136223846793005)
        + UINT64_C(1442695040888963407);
    return *state;
}

uint64_t performance_reference(const int64_t *values, int64_t count) {
    uint64_t sum = 0;
    for (int64_t i = 0; i < count; ++i) {
        if (values[i] >= 0) sum += (uint64_t)values[i];
    }
    return sum;
}

void performance_dataset(int64_t *values, uint64_t *identity,
                         uint64_t *permutation, size_t count,
                         int pattern, uint64_t seed) {
    uint64_t state = seed;
    for (size_t i = 0; i < count; ++i) {
        uint64_t bits = advance(&state);
        int64_t positive = (int64_t)(bits & UINT64_C(0x7fffffffffffffff));
        if (pattern == 0) values[i] = positive;
        else if (pattern == 1) values[i] = (i % 2 == 0) ? positive : -positive - 1;
        else memcpy(&values[i], &bits, sizeof bits);
        identity[i] = (uint64_t)i;
        permutation[i] = (uint64_t)i;
    }
    for (size_t remaining = count; remaining > 1; --remaining) {
        size_t chosen = (size_t)(advance(&state) % (uint64_t)remaining);
        uint64_t saved = permutation[remaining - 1];
        permutation[remaining - 1] = permutation[chosen];
        permutation[chosen] = saved;
    }
}
