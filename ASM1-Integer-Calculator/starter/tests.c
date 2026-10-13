#include "calculator.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

static int64_t signed_bits(uint64_t value) {
    int64_t result;
    memcpy(&result, &value, sizeof(result));
    return result;
}
static uint64_t random_word(uint64_t *state) {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    return *state;
}
static int check(int64_t left, int64_t right, char op, size_t *count) {
    int64_t expected;
    uint64_t a = (uint64_t)left, b = (uint64_t)right;
    switch (op) {
        case '+': expected = signed_bits(a + b); break;
        case '-': expected = signed_bits(a - b); break;
        case '*': expected = signed_bits(a * b); break;
        case '&': expected = signed_bits(a & b); break;
        case '^': expected = signed_bits(a ^ b); break;
        case '/':
            if (right == 0 || (left == INT64_MIN && right == -1)) return 1;
            expected = left / right; break;
        default: return 0;
    }
    const int64_t actual = asm_eval_expression(left, right, op);
    if (actual != expected) {
        fprintf(stderr, "left=%" PRId64 " op=%c right=%" PRId64 ": expected=%" PRId64 " actual=%" PRId64 "\n", left, op, right, expected, actual);
        return 0;
    }
    ++*count;
    return 1;
}
int main(void) {
    const char operations[] = "+-*/&^";
    for (size_t op = 0; op < sizeof(operations) - 1; ++op)
        if (!preserved_registers_ok(12, 5, operations[op])) {
            fputs("callee-saved register contract failed\n", stderr);
            return 1;
        }
    const int64_t values[] = {0, 1, -1, 12, -21, INT64_MIN, INT64_MAX,
        INT64_C(4294967296), -INT64_C(4294967296), INT64_C(0x5555555555555555)};
    size_t count = 0;
    for (size_t a = 0; a < sizeof(values) / sizeof(values[0]); ++a)
        for (size_t b = 0; b < sizeof(values) / sizeof(values[0]); ++b)
            for (size_t op = 0; op < sizeof(operations) - 1; ++op)
                if (!check(values[a], values[b], operations[op], &count)) return 1;
    uint64_t state = UINT64_C(0x12caffee5197a3bd);
    for (size_t i = 0; i < 2000; ++i) {
        int64_t left = signed_bits(random_word(&state));
        int64_t right = signed_bits(random_word(&state));
        for (size_t op = 0; op < sizeof(operations) - 1; ++op)
            if (!check(left, right, operations[op], &count)) return 1;
    }
    if (asm_eval_expression(3, 0, '/') != 0 ||
        asm_eval_expression(INT64_MIN, -1, '/') != 0) {
        fputs("invalid division guard failed\n", stderr);
        return 1;
    }
    printf("%zu calculator cases accepted; invalid divisions guarded\n", count);
    return 0;
}
