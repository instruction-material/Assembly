#include "arithmetic.h"
#include <limits.h>
#include <string.h>
static int64_t signed_bits(uint64_t value) { int64_t out; memcpy(&out, &value, sizeof out); return out; }
static uint64_t bits(int64_t value) { uint64_t out; memcpy(&out, &value, sizeof out); return out; }
static uint64_t status(uint64_t result) { return (result == 0 ? (uint64_t)AR_ZF : 0) | ((result >> 63) != 0 ? (uint64_t)AR_SF : 0); }
static uint64_t signed_product_high(uint64_t a, uint64_t b) {
    uint64_t a0 = (uint32_t)a, a1 = a >> 32, b0 = (uint32_t)b, b1 = b >> 32;
    uint64_t t = a0 * b0;
    uint64_t k = t >> 32;
    t = a1 * b0 + k;
    uint64_t w1 = (uint32_t)t, w2 = t >> 32;
    t = a0 * b1 + w1;
    uint64_t high = a1 * b1 + w2 + (t >> 32);
    if ((a >> 63) != 0) high -= b;
    if ((b >> 63) != 0) high -= a;
    return high;
}
int arithmetic_model(uint32_t op, uint64_t a, uint64_t b, ArithmeticResult *out) {
    if (out == NULL || op >= (uint32_t)AR_OP_COUNT) return 0;
    ArithmeticResult r = {a, 0, 0, AR_ALL_FLAGS};
    uint64_t temp = 0;
    switch (op) {
    case AR_ADD:
        r.value = a + b; r.flags = status(r.value);
        if (r.value < a) r.flags |= AR_CF;
        if (((~(a ^ b) & (a ^ r.value)) >> 63) != 0) r.flags |= AR_OF;
        break;
    case AR_SUB: case AR_CMP:
        temp = a - b; r.flags = status(temp);
        if (a < b) r.flags |= AR_CF;
        if ((((a ^ b) & (a ^ temp)) >> 63) != 0) r.flags |= AR_OF;
        if (op == AR_SUB) r.value = temp;
        break;
    case AR_MUL:
        r.value = a * b; r.auxiliary = signed_product_high(a, b);
        r.defined = AR_MUL_FLAGS;
        if (r.auxiliary != ((r.value >> 63) != 0 ? UINT64_MAX : 0)) r.flags = AR_MUL_FLAGS;
        break;
    case AR_DIV: {
        int64_t left = signed_bits(a), right = signed_bits(b);
        if (right == 0 || (left == INT64_MIN && right == -1)) return 0;
        r.value = bits(left / right); r.auxiliary = bits(left % right); r.defined = 0;
        break;
    }
    case AR_AND: case AR_TEST:
        temp = a & b; r.flags = status(temp);
        if (op == AR_AND) r.value = temp;
        break;
    case AR_OR: r.value = a | b; r.flags = status(r.value); break;
    case AR_XOR: r.value = a ^ b; r.flags = status(r.value); break;
    default: return 0;
    }
    *out = r;
    return 1;
}
uint64_t arithmetic_c_mix(uint64_t left, uint64_t right) { return (left + right) ^ (left & right); }
