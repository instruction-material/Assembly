#include "lab.h"
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    LabRecord records[4];
    LabRecord *pointers[4];
    for (size_t i=0;i<4;++i) {
        records[i].counter=incoming+(uint64_t)i;
        records[i].tag=(uint16_t)(incoming^((uint64_t)i*UINT64_C(0x1111)));
        records[i].state=(uint8_t)i;
        records[i].reserved=UINT8_C(0xa5);
        records[i].weight=(uint32_t)(incoming>>16)^((uint32_t)i*UINT32_C(0x01010101));
        pointers[i]=&records[(i+(size_t)(incoming&UINT64_C(3)))&3];
    }
    const size_t index=(size_t)(initial&UINT64_C(3));
    const LabRecord *selected=pointers[index];
    output->value[0]=(uint64_t)index;
    output->value[1]=selected->state;
    output->value[2]=selected->weight;
    output->value[3]=selected->tag;
    output->value[4]=(uint64_t)(selected-records)*(uint64_t)sizeof(LabRecord);
}
const char *const lab_field_names[LAB_FIELD_COUNT] = {"table-index", "record-index", "weight", "tag", "record-byte-offset"};
