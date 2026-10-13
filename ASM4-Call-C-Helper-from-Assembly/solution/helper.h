#ifndef ASSEMBLY_HELPER_H
#define ASSEMBLY_HELPER_H
#include <stdint.h>

/* count <= 0 is empty and does not read values.
   Positive count requires count readable int32_t elements.
   Sum and scale use their low 64 bits, interpreted as signed before clamping.
   The caller supplies min_value <= max_value.
   Preserve the input and System V callee-saved registers. */
int64_t asm_scaled_clamped_sum(const int32_t *values, int64_t count,
                              int64_t scale, int64_t min_value, int64_t max_value);
int64_t clamp_to_range(int64_t value, int64_t min_value, int64_t max_value);
#endif
