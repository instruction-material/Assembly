#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"selector", "result", "visited-case-mask", "comparisons"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t selector = initial % UINT64_C(4);
    uint64_t result = 0;
    switch (selector) {
    case 0: result = incoming + UINT64_C(11); break;
    case 1: result = incoming ^ UINT64_C(0x55); break;
    case 2: result = incoming - UINT64_C(7); break;
    default: result = incoming; break;
    }
    output->value[0] = selector;
    output->value[1] = result;
    output->value[2] = UINT64_C(1) << selector;
    output->value[3] = selector < UINT64_C(2) ? selector + UINT64_C(1) : UINT64_C(3);
}
