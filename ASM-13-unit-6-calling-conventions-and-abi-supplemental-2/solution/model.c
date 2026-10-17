#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"helper-result", "saved-initial", "saved-incoming"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    const uint64_t a2 = initial ^ incoming;
    const uint64_t a3 = initial + incoming;
    const uint64_t a4 = ~initial;
    const uint64_t a5 = ~incoming;
    uint64_t value = initial + UINT64_C(3) * incoming + UINT64_C(5) * a2
        + UINT64_C(7) * a3 + UINT64_C(11) * a4 + UINT64_C(13) * a5;
    output->value[0] = value;
    output->value[1] = initial;
    output->value[2] = incoming;
}
