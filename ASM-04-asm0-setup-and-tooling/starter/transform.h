#ifndef ASM_TRANSFORM_H
#define ASM_TRANSFORM_H
#include <stdint.h>
/* Linux x86-64 System V ABI: interpret 2 * input + 5 modulo 2^32. */
int32_t transform_value(int32_t input);
#endif
