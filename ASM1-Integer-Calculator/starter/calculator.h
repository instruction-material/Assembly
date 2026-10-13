#ifndef ASSEMBLY_CALCULATOR_H
#define ASSEMBLY_CALCULATOR_H
#include <stdint.h>
/* Valid operators are + - * / & ^. Arithmetic wraps to the low 64 bits,
 * interpreted as signed. Division truncates toward zero and requires a
 * nonzero divisor and a representable signed quotient. */
int64_t asm_eval_expression(int64_t left, int64_t right, char op);
int preserved_registers_ok(int64_t left, int64_t right, char op);
#endif
