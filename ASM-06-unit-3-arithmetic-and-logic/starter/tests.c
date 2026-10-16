#include "arithmetic.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static uint64_t cases;
static int check(uint32_t op, uint64_t a, uint64_t b) {
    ArithmeticResult actual, expected, sentinel;
    memset(&sentinel, 0xa5, sizeof sentinel); actual = sentinel; expected = sentinel;
    int want = arithmetic_model(op, a, b, &expected);
    int got = arithmetic_eval(op, a, b, &actual);
    if (got != want || memcmp(&actual, &expected, sizeof actual) != 0) {
        fprintf(stderr, "mismatch op=%u left=%016" PRIx64 " right=%016" PRIx64 "\n", op, a, b); return 0;
    }
    actual = sentinel;
    if (!preserved_registers_ok(op, a, b, &actual)) { fputs("callee-saved register changed\n", stderr); return 0; }
    if (memcmp(&actual, &expected, sizeof actual) != 0) return 0;
    ++cases; return 1;
}
int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--stream") == 0) {
        unsigned op; uint64_t a, b;
        while (scanf("%u %" SCNx64 " %" SCNx64, &op, &a, &b) == 3) {
            ArithmeticResult r; memset(&r, 0xa5, sizeof r);
            int accepted = arithmetic_eval((uint32_t)op, a, b, &r);
            printf("%d %016" PRIx64 " %016" PRIx64 " %04" PRIx64 " %04" PRIx64 "\n", accepted, r.value, r.auxiliary, r.flags, r.defined);
        }
        return ferror(stdin) ? 2 : 0;
    }
    if (argc != 1) return 2;
    for (uint32_t a = 0; a < 256; ++a) for (uint32_t b = 0; b < 256; ++b) {
        uint64_t left = a < 128 ? a : UINT64_MAX - (255 - a);
        uint64_t right = b < 128 ? b : UINT64_MAX - (255 - b);
        for (uint32_t op = 0; op < (uint32_t)AR_OP_COUNT; ++op) if (!check(op, left, right)) return 1;
    }
    const uint64_t edges[] = {0, 1, 2, 63, 64, 0x7fffffff, 0x80000000, UINT64_C(0x7fffffffffffffff), UINT64_C(0x8000000000000000), UINT64_C(0x8000000000000001), UINT64_MAX - 1, UINT64_MAX};
    for (size_t a = 0; a < sizeof edges / sizeof edges[0]; ++a) for (size_t b = 0; b < sizeof edges / sizeof edges[0]; ++b) {
        for (uint32_t op = 0; op < (uint32_t)AR_OP_COUNT; ++op) if (!check(op, edges[a], edges[b])) return 1;
        if (arithmetic_c_mix(edges[a], edges[b]) != ((edges[a] + edges[b]) ^ (edges[a] & edges[b]))) return 1;
    }
    if (!check(UINT32_MAX, 1, 2) || !check(AR_OP_COUNT, 1, 2)) return 1;
    if (arithmetic_eval(AR_ADD, 1, 2, NULL) != 0 || !preserved_registers_ok(AR_ADD, 1, 2, NULL)) return 1;
    ++cases;
    printf("arithmetic-cases=%" PRIu64 "\n", cases);
    return 0;
}
