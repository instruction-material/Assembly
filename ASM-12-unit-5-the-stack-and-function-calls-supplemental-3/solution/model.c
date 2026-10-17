#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"helper-result", "saved-initial", "saved-incoming", "combined", "helper-entry-alignment"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    output->value[0] = initial ^ incoming;
    output->value[1] = initial;
    output->value[2] = incoming;
    output->value[3] = (initial ^ incoming) + initial;
    output->value[4] = UINT64_C(8);
}
