#include "reverse.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

static int64_t signed_bits(uint64_t bits) {
    int64_t value; memcpy(&value, &bits, sizeof(value)); return value;
}
static int64_t model(int64_t input) {
    uint64_t magnitude = (uint64_t)input;
    if (input < 0) magnitude = UINT64_C(0) - magnitude;
    uint64_t stage = (magnitude & 1) ? magnitude * 3 + 1
        : (magnitude >> 1) | (magnitude & (UINT64_C(1) << 63));
    int64_t signed_stage = signed_bits(stage);
    uint64_t result = signed_stage <= 40 ? stage - 5 : stage + 7;
    return signed_bits(result);
}
static int check(int64_t input, int64_t expected) {
    if (!preserved_mystery_ok(input) || !preserved_reconstruction_ok(input)) {
        fputs("callee-saved register contract failed\n", stderr); return 0;
    }
    const int64_t actual = mystery_score(input), rebuilt = student_reconstruction(input);
    if (actual != expected || rebuilt != expected) {
        fprintf(stderr, "input=%" PRId64 " expected=%" PRId64 " mystery=%" PRId64 " reconstructed=%" PRId64 "\n", input, expected, actual, rebuilt);
        return 0;
    }
    return 1;
}
int main(int argc, char **argv) {
    size_t count = 0;
    if (argc == 2 && strcmp(argv[1], "--oracle") == 0) {
        int64_t input, expected;
        int scanned;
        while ((scanned = scanf("%" SCNd64 " %" SCNd64, &input, &expected)) == 2) {
            if (!check(input, expected)) return 1;
            ++count;
        }
        if (scanned != EOF || !count) return 2;
    } else {
        if (argc != 1) return 2;
        const int64_t fixed[] = {INT64_C(0), INT64_C(1), INT64_C(-1), INT64_C(2), INT64_C(-2), INT64_C(9), INT64_C(-9), INT64_C(4), INT64_C(-4), INT64_C(7), INT64_C(18), INT64_C(32), INT64_C(41), INT64_C(-41), INT64_C(13), INT64_C(-13), INT64_C(15), INT64_C(-15), INT64_C(80), INT64_C(-80), INT64_C(82), INT64_C(-82), INT64_MAX, INT64_MIN, INT64_C(9223372036854775806), INT64_C(-9223372036854775807), INT64_C(4294967296), INT64_C(4294967297), INT64_C(-4294967297), INT64_C(4611686018427387903), INT64_C(4611686018427387904), INT64_C(4611686018427387905), INT64_C(-4611686018427387905)};
        for (size_t i = 0; i < sizeof(fixed) / sizeof(fixed[0]); ++i) {
            if (!check(fixed[i], model(fixed[i]))) return 1;
            ++count;
        }
        uint64_t state = UINT64_C(0x5a17c9e42d0638bf);
        for (size_t i = 0; i < 10000; ++i) {
            state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
            const int64_t input = signed_bits(state);
            if (!check(input, model(input))) return 1;
            ++count;
        }
    }
    printf("reverse cases passed: %zu\n", count);
    return 0;
}
