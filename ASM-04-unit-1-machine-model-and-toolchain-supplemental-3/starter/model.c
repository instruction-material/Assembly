#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"base-plus-index", "base-plus-index-times-2", "base-plus-index-times-4-plus-13", "base-plus-index-times-8-minus-7", "index-times-8"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    output->value[0] = initial + incoming;
    output->value[1] = initial + incoming * UINT64_C(2);
    output->value[2] = initial + incoming * UINT64_C(4) + UINT64_C(13);
    output->value[3] = initial + incoming * UINT64_C(8) - UINT64_C(7);
    output->value[4] = incoming * UINT64_C(8);
}
