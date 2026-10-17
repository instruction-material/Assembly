#include "lab.h"
void lab_operation(uint64_t initial, uint64_t incoming, LabResult *output) {
    uint64_t plain[2] = {initial, incoming};
    uint64_t separate[2] = {initial, incoming};
    const unsigned right_index = (initial & UINT64_C(1)) ? 0U : 1U;
    output->value[0] = compiled_plain(&plain[0], &plain[right_index], incoming);
    output->value[1] = plain[0]; output->value[2] = plain[1];
    output->value[3] = compiled_restricted(&separate[0], &separate[1], incoming);
    output->value[4] = separate[1];
}
