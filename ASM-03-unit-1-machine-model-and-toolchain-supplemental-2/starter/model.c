#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"byte-at-0", "word-at-1", "dword-at-4", "qword-at-0", "cross-qword-at-3", "qword-at-8"};
static uint64_t little_word(const unsigned char *bytes, size_t count) {
    uint64_t result = 0;
    for (size_t index = 0; index < count; ++index)
        result |= (uint64_t)bytes[index] << (index * 8U);
    return result;
}
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    unsigned char bytes[16];
    for (size_t index = 0; index < 8U; ++index) {
        bytes[index] = (unsigned char)(initial >> (index * 8U));
        bytes[index + 8U] = (unsigned char)(incoming >> (index * 8U));
    }
    const size_t offsets[] = {0, 1, 4, 0, 3, 8};
    const size_t widths[] = {1, 2, 4, 8, 8, 8};
    for (size_t index = 0; index < LAB_FIELD_COUNT; ++index)
        output->value[index] = little_word(bytes + offsets[index], widths[index]);
}
