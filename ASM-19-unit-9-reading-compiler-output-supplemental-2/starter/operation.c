#include "lab.h"
#include <string.h>
void lab_operation(uint64_t initial, uint64_t incoming, LabResult *output) {
    const unsigned index = (unsigned)(initial & UINT64_C(7));
    const uint8_t raw = (uint8_t)(incoming >> (index * 8U));
    int8_t signed_value;
    memcpy(&signed_value, &raw, sizeof(signed_value));
    const int threshold = (int)((initial >> 8U) & UINT64_C(255)) - 128;
    output->value[0] = index;
    output->value[1] = (uint64_t)(int64_t)signed_value;
    output->value[2] = raw;
    output->value[3] = (uint64_t)compiled_signed_compare(signed_value, threshold);
    output->value[4] = (uint64_t)compiled_unsigned_compare(raw, threshold);
}
