#define _GNU_SOURCE
#include "parser.h"
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int preserved_parse_ok(const char *, int64_t *);
int preserved_streq_ok(const char *, const char *);
static unsigned parses, equalities;
static int model(const char *text, int64_t *out) {
    size_t i = (text[0] == '+' || text[0] == '-') ? 1 : 0;
    if (!text[i]) return 0;
    for (; text[i]; ++i) if (text[i] < '0' || text[i] > '9') return 0;
    errno = 0;
    char *end = NULL;
    const intmax_t value = strtoimax(text, &end, 10);
    if (errno == ERANGE || end == text || *end || value < INT64_MIN || value > INT64_MAX) return 0;
    *out = (int64_t)value;
    return 1;
}
static int parse_case(const char *text, int64_t *slot) {
    char before[128];
    const size_t length = strlen(text);
    if (length >= sizeof(before)) abort();
    memcpy(before, text, length + 1);
    int64_t expected = INT64_C(123456789);
    const int wanted = model(text, &expected);
    *slot = INT64_C(123456789);
    const int actual = asm_parse_i64(text, slot);
    if (actual != wanted || *slot != expected) {
        fprintf(stderr, "expected success=%d value=%" PRId64 " actual=%d value=%" PRId64 "\n",
                wanted, expected, actual, *slot);
        return 0;
    }
    if (!preserved_parse_ok(text, slot)) {
        fputs("callee-saved register contract failed\n", stderr);
        return 0;
    }
    if (*slot != expected || memcmp(before, text, length + 1)) {
        fputs("parse output or unchanged input contract failed\n", stderr);
        return 0;
    }
    ++parses;
    return 1;
}
static int equality_case(const char *left, const char *right) {
    char a[128], b[128];
    const size_t al = strlen(left), bl = strlen(right);
    if (al >= sizeof(a) || bl >= sizeof(b)) abort();
    memcpy(a, left, al + 1); memcpy(b, right, bl + 1);
    const int wanted = strcmp(left, right) == 0;
    if (asm_streq(left, right) != wanted ||
        !preserved_streq_ok(left, right) ||
        memcmp(a, left, al + 1) || memcmp(b, right, bl + 1)) {
        fputs("equality or preserved-register contract failed\n", stderr);
        return 0;
    }
    ++equalities;
    return 1;
}
static int guard_case(const char *text) {
    const long size = sysconf(_SC_PAGESIZE);
    if (size <= 0) return 0;
    const size_t page = (size_t)size, length = strlen(text);
    unsigned char *input = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (input == MAP_FAILED) return 0;
    char *string = (char *)(input + page - length - 1);
    memcpy(string, text, length + 1);
    if (mprotect(input + page, page, PROT_NONE) || mprotect(input, page, PROT_READ)) {
        munmap(input, 2 * page); return 0;
    }
    unsigned char *output = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (output == MAP_FAILED) { munmap(input, 2 * page); return 0; }
    if (mprotect(output + page, page, PROT_NONE)) {
        munmap(input, 2 * page); munmap(output, 2 * page); return 0;
    }
    int64_t *slot = (int64_t *)(output + page - sizeof(int64_t));
    const int okay = parse_case(string, slot) && equality_case(string, string);
    const int a = munmap(input, 2 * page), b = munmap(output, 2 * page);
    return okay && !a && !b;
}
int main(void) {
    _Static_assert(sizeof(int64_t) == sizeof(uint64_t), "64-bit bit pattern");
    const char *fixed[] = {
        "", "+", "-", "0", "-0", "+0", "0000000000000000000000000000000000000",
        "1", "-1", "+42", "9223372036854775807", "-9223372036854775808",
        "+9223372036854775807", "9223372036854775808", "-9223372036854775809",
        "18446744073709551616", "99999999999999999999999999999999999999",
        "1x", " 1", "1 ", "1\n", "++1", "--1", "+-1", "0x10",
        "-0009223372036854775808", "+0009223372036854775807", "\x80"
    };
    int64_t slot;
    for (size_t i = 0; i < sizeof(fixed) / sizeof(fixed[0]); ++i)
        if (!parse_case(fixed[i], &slot) || !guard_case(fixed[i])) return 1;
    const char *words[] = {"", "sum", "max", "xor", "SUM", "summ", "\x80\xff"};
    for (size_t i = 0; i < 7; ++i)
        for (size_t j = 0; j < 7; ++j)
            if (!equality_case(words[i], words[j])) return 1;
    uint64_t state = UINT64_C(0x123456789abcdef0);
    for (unsigned i = 0; i < 2000; ++i) {
        state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        int64_t value;
        memcpy(&value, &state, sizeof(value));
        char text[32], zeros[64], invalid[64];
        snprintf(text, sizeof(text), "%" PRId64, value);
        snprintf(zeros, sizeof(zeros), "%s000%s", value < 0 ? "-" : "+", value < 0 ? text + 1 : text);
        snprintf(invalid, sizeof(invalid), "%" PRId64 "x", value);
        if (!parse_case(text, &slot) || !parse_case(zeros, &slot) ||
            !parse_case(invalid, &slot)) return 1;
        snprintf(invalid, sizeof(invalid), "%s ", text);
        if (!parse_case(invalid, &slot)) return 1;
    }
    for (unsigned i = 0; i < 512; ++i) {
        char a[65], b[65];
        const size_t length = i % 65;
        for (size_t j = 0; j < length; ++j) a[j] = (char)('a' + (int)((j + i) % 26));
        a[length] = 0; memcpy(b, a, length + 1);
        if (!equality_case(a, b)) return 1;
        if (length) b[length - 1] = b[length - 1] == 'z' ? 'a' : (char)(b[length - 1] + 1);
        else b[0] = 'x', b[1] = 0;
        if (!equality_case(a, b)) return 1;
    }
    printf("%u parse cases and %u equality cases accepted; outputs and bounds verified\n", parses, equalities);
    return 0;
}
