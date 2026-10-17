#ifndef MEMORY_LAYOUT_LAB_H
#define MEMORY_LAYOUT_LAB_H
#include <stddef.h>
#include <stdint.h>
enum { LAB_FIELD_COUNT = 5 };
typedef struct { uint64_t value[LAB_FIELD_COUNT]; } LabResult;
_Static_assert(sizeof(LabResult) == LAB_FIELD_COUNT * sizeof(uint64_t), "Eight-byte field layout required");
typedef struct { uint64_t counter; uint16_t tag; uint8_t state; uint8_t reserved; uint32_t weight; } LabRecord;
_Static_assert(sizeof(LabRecord)==16 && offsetof(LabRecord,tag)==8 && offsetof(LabRecord,state)==10 && offsetof(LabRecord,reserved)==11 && offsetof(LabRecord,weight)==12, "Pinned record layout required");
extern const char *const lab_field_names[LAB_FIELD_COUNT];
void lab_operation(uint64_t initial, uint64_t incoming, LabResult *output);
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output);
void abi_probe(void (*routine)(uint64_t, uint64_t, LabResult *), uint64_t initial, uint64_t incoming, LabResult *output, int *preserved);
#endif
