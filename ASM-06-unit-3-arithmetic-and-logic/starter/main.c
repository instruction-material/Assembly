#include "arithmetic.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static const char *names[] = {"add", "sub", "imul", "idiv", "and", "or", "xor", "test", "cmp"};
int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed") != 0)) {
        fputs("usage: assembly_arithmetic [--changed]\n", stderr); return 2;
    }
    uint64_t a[] = {UINT64_C(0x7fffffffffffffff), 0, UINT64_C(0x8000000000000000), UINT64_C(0xffffffffffffffeb), 0xf0, 0xf0, 0xff, 0xf0, UINT64_C(0x8000000000000000)};
    uint64_t b[] = {1, 1, UINT64_MAX, 4, 0x0f, 0x0f, 0xff, 0x0f, 1};
    if (argc == 2) {
        a[0] = UINT64_MAX; b[0] = 1;
        a[1] = UINT64_C(0x8000000000000000); b[1] = 1;
        a[2] = UINT64_MAX; b[2] = 2;
        a[3] = 21; b[3] = UINT64_C(0xfffffffffffffffc);
        a[4] = 0x80; b[4] = 0xff;
        a[5] = 0; b[5] = UINT64_C(0x8000000000000000);
        a[6] = UINT64_MAX; b[6] = 0;
        a[7] = 0x80; b[7] = 0x80;
        a[8] = 1; b[8] = UINT64_C(0x8000000000000000);
    }
    ArithmeticResult results[AR_OP_COUNT];
    for (uint32_t op = 0; op < (uint32_t)AR_OP_COUNT; ++op) {
        ArithmeticResult expected;
        if (!arithmetic_eval(op, a[op], b[op], &results[op])) {
            fputs("Unfinished ARITH_MUL/ARITH_DIV; complete routine.S and retain this exit-78 result.\n", stderr); return 78;
        }
        if (!arithmetic_model(op, a[op], b[op], &expected) || memcmp(&expected, &results[op], sizeof expected) != 0) {
            fputs("arithmetic contract mismatch\n", stderr); return 1;
        }
    }
    for (uint32_t op = 0; op < (uint32_t)AR_OP_COUNT; ++op) {
        ArithmeticResult r = results[op];
        printf("op=%s left=%016" PRIx64 " right=%016" PRIx64 " value=%016" PRIx64 " auxiliary=%016" PRIx64 " flags=%04" PRIx64 " defined=%04" PRIx64 "\n", names[op], a[op], b[op], r.value, r.auxiliary, r.flags, r.defined);
    }
    printf("c-mix=%016" PRIx64 "\n", arithmetic_c_mix(a[0], b[0]));
    return 0;
}
