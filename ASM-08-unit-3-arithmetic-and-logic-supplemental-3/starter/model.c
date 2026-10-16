#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"left", "logical-right", "arithmetic-right", "effective-count"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const unsigned count = (unsigned)(incoming & UINT64_C(63));
    const uint64_t logical = initial >> count;
    const uint64_t extension = (initial & (UINT64_C(1) << 63)) ? ~(UINT64_MAX >> count) : UINT64_C(0);
    output->value[0] = initial << count;
    output->value[1] = logical;
    output->value[2] = logical | extension;
    output->value[3] = (uint64_t)count;
}
