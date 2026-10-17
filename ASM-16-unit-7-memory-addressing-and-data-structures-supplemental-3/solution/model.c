#include "lab.h"
#include <string.h>
void lab_model(uint64_t initial, uint64_t incoming, LabResult *output) {
    unsigned char data[16];
    for (size_t i=0;i<16;++i) data[i]=(unsigned char)(i+1);
    const size_t source=(size_t)(initial&UINT64_C(7));
    const size_t destination=(size_t)(incoming&UINT64_C(7));
    size_t count=(size_t)((initial>>3)&UINT64_C(15));
    if (count>16-source) count=16-source;
    if (count>16-destination) count=16-destination;
    memmove(data+destination,data+source,count);
    output->value[0]=UINT64_C(0); output->value[1]=UINT64_C(0);
    for (size_t i=0;i<8;++i) {
        output->value[0]|=(uint64_t)data[i]<<(i*8);
        output->value[1]|=(uint64_t)data[i+8]<<(i*8);
    }
    output->value[2]=(uint64_t)count;
    output->value[3]=(uint64_t)source;
    output->value[4]=(uint64_t)destination;
}
const char *const lab_field_names[LAB_FIELD_COUNT] = {"bytes-0-through-7", "bytes-8-through-15", "copied-count", "source-offset", "destination-offset"};
