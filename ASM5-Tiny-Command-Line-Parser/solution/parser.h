#ifndef ASSEMBLY_PARSER_H
#define ASSEMBLY_PARSER_H
#include <stdint.h>

/* Inputs are readable through NUL. Equality returns exactly 0 or 1.
   Decimal grammar: optional + or -, then at least one ASCII digit, then NUL.
   Parse succeeds only within INT64_MIN..INT64_MAX, writes one int64_t and returns 1.
   Failure returns 0 and leaves the writable output slot unchanged.
   Both routines preserve input bytes and System V callee-saved registers. */
int asm_streq(const char *left, const char *right);
int asm_parse_i64(const char *text, int64_t *out_value);
#endif
