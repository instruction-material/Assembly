#include "model.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static int64_t signed_bits(uint64_t bits) {
    int64_t result; memcpy(&result,&bits,sizeof(result)); return result;
}
static int check(int64_t value, int64_t factor, int64_t bias, int64_t expected) {
    if (!preserved_compiled_ok(value,factor,bias)) {
        fputs("callee-saved register contract failed\n",stderr); return 0;
    }
    const int64_t actual=compiled_score(value,factor,bias);
    if (actual!=expected) {
        fprintf(stderr,"value=%" PRId64 " factor=%" PRId64 " bias=%" PRId64 " expected=%" PRId64 " actual=%" PRId64 "\n",value,factor,bias,expected,actual); return 0;
    }
    return 1;
}
int main(int argc,char **argv) {
    size_t count=0;
    if (argc==2 && strcmp(argv[1],"--oracle")==0) {
        int scanned; int64_t v,f,b,e;
        while ((scanned=scanf("%" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64,&v,&f,&b,&e))==4) {
            if (!check(v,f,b,e)) return 1;
            ++count;
        }
        if (scanned!=EOF || !count) return 2;
    } else {
        if (argc!=1) return 2;
        const int64_t fixed[][3]={{0,0,0},{6,7,-5},{-9,3,1},{INT64_MAX,2,7},{INT64_MIN,-1,0},{INT64_MIN,0,INT64_MAX},{INT64_MAX,INT64_MAX,INT64_MIN},{INT64_MIN,INT64_MIN,INT64_MAX},{INT64_MAX,1,0},{INT64_C(4294967296),INT64_C(4294967296),1},{-INT64_C(4294967296),3,-7},{3,-INT64_C(4294967296),INT64_C(4294967296)},{1,0,-1}};
        for (size_t i=0;i<sizeof(fixed)/sizeof(fixed[0]);++i) {
            const int64_t v=fixed[i][0],f=fixed[i][1],b=fixed[i][2];
            if (!check(v,f,b,signed_bits((uint64_t)v*(uint64_t)f+(uint64_t)b))) return 1;
            ++count;
        }
        uint64_t state=UINT64_C(0x4bc392e105a67d8f);
        for (size_t i=0;i<10000;++i) {
            state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); const int64_t v=signed_bits(state);
            state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); const int64_t f=signed_bits(state);
            state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); const int64_t b=signed_bits(state);
            if (!check(v,f,b,signed_bits((uint64_t)v*(uint64_t)f+(uint64_t)b))) return 1;
            ++count;
        }
    }
    printf("compiler cases passed: %zu\n",count); return 0;
}
