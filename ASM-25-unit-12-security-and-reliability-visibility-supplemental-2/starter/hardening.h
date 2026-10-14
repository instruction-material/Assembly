#ifndef ASSEMBLY_HARDENING_H
#define ASSEMBLY_HARDENING_H
#include <stdint.h>
/* Counts outside 1..32 return zero without accessing input. */
uint64_t checksum_c(const uint8_t *input, int64_t count);
uint64_t checksum_asm(const uint8_t *input, int64_t count);
int preserved_c_ok(const uint8_t *input, int64_t count);
int preserved_asm_ok(const uint8_t *input, int64_t count);
#endif
