#include "parser.h"
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int validate_decimal(const char *text, int64_t *out) {
    size_t i = (text[0] == '+' || text[0] == '-') ? 1 : 0;
    if (text[i] == 0) return 0;
    for (; text[i] != 0; ++i) if (text[i] < '0' || text[i] > '9') return 0;
    errno = 0;
    char *end = NULL;
    const intmax_t value = strtoimax(text, &end, 10);
    if (errno == ERANGE || end == text || *end || value < INT64_MIN || value > INT64_MAX) return 0;
    *out = (int64_t)value;
    return 1;
}
static int ready(void) {
    int64_t value = 91;
    if (!asm_parse_i64("-1", &value) || value != -1) return 0;
    if (!asm_parse_i64("+9223372036854775807", &value) || value != INT64_MAX) return 0;
    if (!asm_parse_i64("-9223372036854775808", &value) || value != INT64_MIN) return 0;
    value = 91;
    if (asm_parse_i64("9223372036854775808", &value) || value != 91) return 0;
    return asm_streq("sum", "sum") == 1 && asm_streq("sum", "SUM") == 0 &&
           asm_streq("", "") == 1;
}
static int unfinished(void) {
    fputs("Parser unfinished or incorrect; complete PARSE_SIGN and PARSE_BOUND and run the contracts.\n", stderr);
    return 78;
}
static int invalid(void) {
    fputs("Use <sum|max|xor> with at least two signed decimal 64-bit operands.\n", stderr);
    return 2;
}
int main(int argc, char **argv) {
    if (argc == 1) {
        if (!ready()) return unfinished();
        const char *samples[] = {"12", "-4", "7"};
        uint64_t sum_bits = 0, xor_bits = 0;
        int64_t maximum = INT64_MIN;
        for (size_t i = 0; i < 3; ++i) {
            int64_t parsed = 91;
            if (!asm_parse_i64(samples[i], &parsed)) return unfinished();
            sum_bits += (uint64_t)parsed;
            xor_bits ^= (uint64_t)parsed;
            if (parsed > maximum) maximum = parsed;
        }
        int64_t sum, xored;
        memcpy(&sum, &sum_bits, sizeof(sum));
        memcpy(&xored, &xor_bits, sizeof(xored));
        if (sum != 15 || maximum != 12 || xored != -9) return unfinished();
        printf("sum=%" PRId64 "\nmax=%" PRId64 "\nxor=%" PRId64 "\n", sum, maximum, xored);
        return 0;
    }
    if (argc < 4 || (strcmp(argv[1], "sum") && strcmp(argv[1], "max") && strcmp(argv[1], "xor"))) return invalid();
    for (int i = 2; i < argc; ++i) {
        int64_t expected;
        if (!validate_decimal(argv[i], &expected)) return invalid();
    }
    if (!ready()) return unfinished();
    uint64_t bits = 0;
    int64_t maximum = INT64_MIN;
    for (int i = 2; i < argc; ++i) {
        int64_t expected, value = 91;
        if (!validate_decimal(argv[i], &expected) || !asm_parse_i64(argv[i], &value) || value != expected) return unfinished();
        if (asm_streq(argv[1], "sum")) bits += (uint64_t)value;
        else if (asm_streq(argv[1], "max")) { if (value > maximum) maximum = value; }
        else bits ^= (uint64_t)value;
    }
    int64_t result;
    memcpy(&result, &bits, sizeof(result));
    if (asm_streq(argv[1], "max")) result = maximum;
    printf("result=%" PRId64 "\n", result);
    return 0;
}
