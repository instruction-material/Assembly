#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"byte-signed", "byte-unsigned", "word-signed", "word-unsigned", "dword-signed", "dword-unsigned"};
static uint64_t signed_pattern(uint64_t incoming, unsigned bits) {
    const uint64_t modulus = UINT64_C(1) << bits;
    const uint64_t low = incoming & (modulus - 1);
    const int64_t value = (low & (modulus >> 1)) ? (int64_t)low - (int64_t)modulus : (int64_t)low;
    return (uint64_t)value;
}
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    (void)initial;
    output->value[0] = signed_pattern(incoming, 8);
    output->value[1] = incoming & UINT64_C(0xff);
    output->value[2] = signed_pattern(incoming, 16);
    output->value[3] = incoming & UINT64_C(0xffff);
    output->value[4] = signed_pattern(incoming, 32);
    output->value[5] = incoming & UINT64_C(0xffffffff);
}
