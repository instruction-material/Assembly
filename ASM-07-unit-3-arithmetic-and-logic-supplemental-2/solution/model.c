#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"unsigned-below", "unsigned-below-equal", "signed-less", "signed-less-equal", "equal", "not-equal"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t left_order = initial ^ (UINT64_C(1) << 63);
    const uint64_t right_order = incoming ^ (UINT64_C(1) << 63);
    output->value[0] = initial < incoming ? UINT64_C(1) : UINT64_C(0);
    output->value[1] = initial <= incoming ? UINT64_C(1) : UINT64_C(0);
    output->value[2] = left_order < right_order ? UINT64_C(1) : UINT64_C(0);
    output->value[3] = left_order <= right_order ? UINT64_C(1) : UINT64_C(0);
    output->value[4] = initial == incoming ? UINT64_C(1) : UINT64_C(0);
    output->value[5] = initial != incoming ? UINT64_C(1) : UINT64_C(0);
}
