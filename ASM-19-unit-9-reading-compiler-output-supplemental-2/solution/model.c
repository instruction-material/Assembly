#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"byte_index", "signed_bits", "unsigned_value", "signed_less", "unsigned_less"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t index = initial & UINT64_C(7);
    const int64_t raw = (int64_t)((incoming >> (8U * index)) & UINT64_C(255));
    const int64_t signed_value = raw >= 128 ? raw - 256 : raw;
    const int64_t threshold = (int64_t)((initial >> 8U) & UINT64_C(255)) - 128;
    output->value[0] = index; output->value[1] = (uint64_t)signed_value;
    output->value[2] = (uint64_t)raw;
    output->value[3] = (uint64_t)(signed_value < threshold);
    output->value[4] = (uint64_t)(raw < threshold);
}
