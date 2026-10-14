#include "model.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const int64_t inputs[][3] = {{6,7,-5},{-9,3,1},{INT64_MAX,2,7},{INT64_MIN,-1,0}};
    for (size_t i=0;i<sizeof(inputs)/sizeof(inputs[0]);++i) {
        const int64_t value=inputs[i][0], factor=inputs[i][1], bias=inputs[i][2];
        const uint64_t bits=(uint64_t)value*(uint64_t)factor+(uint64_t)bias;
        int64_t expected; memcpy(&expected,&bits,sizeof(expected));
        if (compiled_score(value,factor,bias)!=expected) {
            fputs("Compiler model contract failed.\n",stderr); return 1;
        }
    }
    for (size_t i=0;i<sizeof(inputs)/sizeof(inputs[0]);++i)
        printf("value=%" PRId64 " factor=%" PRId64 " bias=%" PRId64 " result=%" PRId64 "\n",inputs[i][0],inputs[i][1],inputs[i][2],compiled_score(inputs[i][0],inputs[i][1],inputs[i][2]));
    return 0;
}
