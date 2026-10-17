#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"first-pop", "second-pop", "initial-minus-incoming", "stack-delta"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    output->value[0] = incoming;
    output->value[1] = initial;
    output->value[2] = initial - incoming;
    output->value[3] = UINT64_C(0);
}
