#include "transform.h"
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

_Static_assert(CHAR_BIT == 8 && sizeof(int32_t) == 4, "32-bit byte model");

static int32_t from_bits(uint32_t bits) {
    int32_t value;
    memcpy(&value, &bits, sizeof value);
    return value;
}

static int check(uint32_t bits) {
    const int32_t input = from_bits(bits);
    const int32_t expected = from_bits(bits * UINT32_C(2) + UINT32_C(5));
    const int32_t actual = transform_value(input);
    if (actual != expected) {
        fprintf(stderr, "input=%" PRId32 ": expected=%" PRId32
                        " actual=%" PRId32 "\n", input, expected, actual);
        return 0;
    }
    return 1;
}

extern int preserved_registers_ok(void);

int main(void) {
    if (!preserved_registers_ok()) {
        fputs("callee-saved register contract failed\n", stderr);
        return 1;
    }
    const uint32_t fixed[] = {0, 1, UINT32_MAX, UINT32_C(0x80000000),
        UINT32_C(0x7fffffff), UINT32_C(0xfffffffb), UINT32_C(0x3ffffffd),
        UINT32_C(0xbfffffff), 3, 7, 11, 19};
    for (size_t i = 0; i < sizeof fixed / sizeof fixed[0]; ++i)
        if (!check(fixed[i])) return 1;
    uint32_t state = UINT32_C(123456789);
    for (size_t i = 0; i < 10000; ++i) {
        state = state * UINT32_C(1664525) + UINT32_C(1013904223);
        if (!check(state)) return 1;
    }
    puts("10012 transform cases accepted");
    return 0;
}
