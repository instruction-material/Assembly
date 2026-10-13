#include "calculator.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_operand(const char *text, int64_t *value) {
    const char *digits = text;
    if (*digits == '-' || *digits == '+') ++digits;
    if (!*digits) return 0;
    for (const char *p = digits; *p; ++p)
        if (*p < '0' || *p > '9') return 0;
    errno = 0;
    char *end = NULL;
    intmax_t parsed = strtoimax(text, &end, 10);
    if (errno == ERANGE || *end || parsed < INT64_MIN || parsed > INT64_MAX)
        return 0;
    *value = (int64_t)parsed;
    return 1;
}
static int valid_expression(int64_t left, int64_t right, char op) {
    return strchr("+-*/&^", op) != NULL && op != '\0' &&
        (op != '/' || (right != 0 && !(left == INT64_MIN && right == -1)));
}
static int implementation_ready(void) {
    const struct { int64_t left, right, expected; char op; } probes[] = {
        {12, 5, 17, '+'}, {12, 5, 7, '-'}, {7, 6, 42, '*'},
        {21, 3, 7, '/'}, {42, 15, 10, '&'}, {42, 15, 37, '^'},
        {-21, 3, -7, '/'}, {-21, -3, 7, '/'}
    };
    for (size_t i = 0; i < sizeof(probes) / sizeof(probes[0]); ++i)
        if (asm_eval_expression(probes[i].left, probes[i].right, probes[i].op)
            != probes[i].expected) return 0;
    return 1;
}
int main(int argc, char **argv) {
    int64_t left = 0, right = 0;
    char op = '\0';
    if (argc != 1) {
        if (argc != 4 || strlen(argv[1]) != 1 ||
            !parse_operand(argv[2], &left) || !parse_operand(argv[3], &right) ||
            !valid_expression(left, right, argv[1][0])) {
            fputs("Use one of + - * / & ^ and two signed decimal 64-bit operands; division must have a nonzero divisor and a representable quotient.\n", stderr);
            return 2;
        }
        op = argv[1][0];
    }
    if (!implementation_ready()) {
        fputs("Calculator implementation unfinished or incorrect: complete CALC_DIV, CALC_AND and CALC_XOR.\n", stderr);
        return 78;
    }
    if (argc == 4) {
        printf("result=%" PRId64 "\n", asm_eval_expression(left, right, op));
        return 0;
    }
    const struct { int64_t left, right; char op; } cases[] = {
        {12, 5, '+'}, {12, 5, '-'}, {7, 6, '*'},
        {21, 3, '/'}, {42, 15, '&'}, {42, 15, '^'}
    };
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i)
        printf("%" PRId64 " %c %" PRId64 " => %" PRId64 "\n",
            cases[i].left, cases[i].op, cases[i].right,
            asm_eval_expression(cases[i].left, cases[i].right, cases[i].op));
    return 0;
}
