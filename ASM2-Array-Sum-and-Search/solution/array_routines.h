#ifndef ARRAY_ROUTINES_H
#define ARRAY_ROUTINES_H
#include <stdint.h>

/* count <= 0: return 0 / -1 without reading values.
   count > 0: values points to at least count readable int32_t elements.
   Sum returns the signed interpretation of its low 64 bits.
   Search returns the first signed >= threshold index, or -1.
   Both functions preserve the input and System V callee-saved registers. */
int64_t asm_sum_array(const int32_t *values, int64_t count);
int64_t asm_find_first_ge(const int32_t *values, int64_t count, int32_t threshold);
#endif
