#include "lab.h"
#include <inttypes.h>
#include <stdio.h>

static int check(uint64_t initial, uint64_t incoming, size_t index) {
    LabResult actual = {0}, expected = {0};
    int preserved = 0;
    lab_model(initial, incoming, &expected);
    abi_probe(lab_operation, initial, incoming, &actual, &preserved);
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field) {
        if (!preserved || actual.value[field] != expected.value[field]) {
            fprintf(stderr, "case=%zu field=%zu actual=%016" PRIx64 " expected=%016" PRIx64 " preserved=%d\n", index, field, actual.value[field], expected.value[field], preserved);
            return 0;
        }
    }
    return 1;
}

int main(void) {
    const uint64_t fixed[] = {0, 1, 0x7f, 0x80, 0xff, 0x7fff, 0x8000, 0xffff,
        0x7fffffff, 0x80000000, 0xffffffff, UINT64_C(0x100000000),
        UINT64_C(0x1122334455667788), UINT64_C(0xaabbccddeeff80ff),
        UINT64_C(0xaaaaaaaaaaaaaaaa), UINT64_MAX};
    size_t cases = 0;
    for (size_t i = 0; i < sizeof fixed / sizeof fixed[0]; ++i)
        for (size_t j = 0; j < sizeof fixed / sizeof fixed[0]; ++j) {
            if (!check(fixed[i], fixed[j], cases)) return 1;
            ++cases;
        }
    uint64_t state = UINT64_C(0x41c64e6d12345678);
    for (size_t i = 0; i < 10013; ++i) {
        state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        const uint64_t initial = state;
        state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        if (!check(initial, state, cases)) return 1;
        ++cases;
    }
    printf("%zu independent width cases; %u fields; six preserved registers accepted\n", cases, (unsigned)LAB_FIELD_COUNT);
    return 0;
}
