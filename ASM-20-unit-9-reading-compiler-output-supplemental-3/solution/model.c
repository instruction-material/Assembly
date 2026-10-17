#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"plain_return", "plain_left", "plain_second_slot", "restricted_return", "restricted_right"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t updated = initial + incoming;
    const uint64_t plain_left = (initial & UINT64_C(1)) ? 0 : updated;
    output->value[0] = plain_left; output->value[1] = plain_left;
    output->value[2] = (initial & UINT64_C(1)) ? incoming : (incoming ^ updated);
    output->value[3] = updated; output->value[4] = incoming ^ updated;
}
