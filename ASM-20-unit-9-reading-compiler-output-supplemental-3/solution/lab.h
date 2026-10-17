#ifndef COMPILER_OBSERVATION_LAB_H
#define COMPILER_OBSERVATION_LAB_H
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
_Static_assert(CHAR_BIT == 8 && INT8_MIN == -128 && INT8_MAX == 127, "Eight-bit exact signed representation required");
_Static_assert(sizeof(int) == 4 && INT_MAX == 2147483647, "Linux x86-64 integer promotions required");
enum { LAB_FIELD_COUNT = 5 };
typedef struct { uint64_t value[LAB_FIELD_COUNT]; } LabResult;
extern const char *const lab_field_names[LAB_FIELD_COUNT];
void lab_operation(uint64_t initial, uint64_t incoming, LabResult *output);
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output);
void abi_probe(void (*routine)(uint64_t, uint64_t, LabResult *), uint64_t initial, uint64_t incoming, LabResult *output, int *preserved);
uint64_t compiled_plain(uint64_t *left, uint64_t *right, uint64_t delta);
uint64_t compiled_restricted(uint64_t *restrict left, uint64_t *restrict right, uint64_t delta);
#endif
