#include "hardening.h"
#include <stddef.h>

uint64_t checksum_c(const uint8_t *input, int64_t count) {
    if (count <= 0 || count > 32) return 0;
    /* Volatile keeps the bounded local buffer visible at both opt levels. */
    volatile uint8_t scratch[32];
    for (int64_t i = 0; i < count; ++i) scratch[i] = input[i];
    uint64_t value = UINT64_C(5381);
    for (int64_t i = 0; i < count; ++i) {
        value = value * UINT64_C(33) + scratch[i];
    }
    return value;
}
