#include "reverse.h"
#include <string.h>

static int64_t signed_bits(uint64_t bits) {
    int64_t value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

int64_t student_reconstruction(int64_t value) {
    uint64_t bits = (uint64_t)value;
    if (value < 0) bits = UINT64_C(0) - bits;
    if ((bits & UINT64_C(1)) != 0) bits = bits * UINT64_C(3) + UINT64_C(1);
    else bits = (bits >> 1) | (bits & (UINT64_C(1) << 63));
    return signed_bits(bits + (signed_bits(bits) > 40 ? UINT64_C(7)
                               : UINT64_C(0) - UINT64_C(5)));
}
