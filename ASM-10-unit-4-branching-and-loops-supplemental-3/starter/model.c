#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"count", "sum", "body-visits", "visited-index-mask", "exit-index"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t count = initial % UINT64_C(16);
    output->value[0] = count;
    output->value[1] = count * incoming;
    output->value[2] = count;
    output->value[3] = (UINT64_C(1) << count) - UINT64_C(1);
    output->value[4] = count;
}
