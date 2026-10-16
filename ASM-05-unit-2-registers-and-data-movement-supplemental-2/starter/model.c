#include "lab.h"
const char *const lab_field_names[LAB_FIELD_COUNT] = {"byte", "word", "dword", "qword"};
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    output->value[0] = (initial & ~UINT64_C(0xff)) | (incoming & UINT64_C(0xff));
    output->value[1] = (initial & ~UINT64_C(0xffff)) | (incoming & UINT64_C(0xffff));
    output->value[2] = incoming & UINT64_C(0xffffffff);
    output->value[3] = incoming;
}
