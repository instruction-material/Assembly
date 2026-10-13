#include "stack.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
uint64_t stack_call_count;
int64_t stack_arguments[2];
int stack_alignment_bad, stack_excess_calls;
static int64_t signed_bits(uint64_t bits) {
    int64_t result; memcpy(&result,&bits,sizeof(result)); return result;
}
static void reset(void) {
    stack_call_count = 0; stack_arguments[0] = 91; stack_arguments[1] = 92;
    stack_alignment_bad = 0; stack_excess_calls = 0;
}
static int calls_ok(int64_t a, int64_t b) {
    if (stack_call_count != 2 || stack_arguments[0] != a || stack_arguments[1] != b || stack_alignment_bad || stack_excess_calls) {
        fputs("nested-call count, arguments or stack alignment failed\n",stderr); return 0;
    }
    return 1;
}
static int check(int64_t a, int64_t b, int64_t expected) {
    reset();
    if (!preserved_stack_ok(a,b)) { fputs("callee-saved register contract failed\n",stderr); return 0; }
    if (!calls_ok(a,b)) return 0;
    reset(); const int64_t actual = stack_pair(a,b);
    if (!calls_ok(a,b)) return 0;
    if (actual != expected) {
        fprintf(stderr,"a=%" PRId64 " b=%" PRId64 " expected=%" PRId64 " actual=%" PRId64 "\n",a,b,expected,actual); return 0;
    }
    return 1;
}
int main(int argc, char **argv) {
    size_t count = 0;
    if (argc == 2 && strcmp(argv[1],"--oracle") == 0) {
        int scanned; int64_t a,b,expected;
        while ((scanned = scanf("%" SCNd64 " %" SCNd64 " %" SCNd64,&a,&b,&expected)) == 3) {
            if (!check(a,b,expected)) return 1;
            ++count;
        }
        if (scanned != EOF || !count) return 2;
    } else {
        if (argc != 1) return 2;
        const int64_t fixed[][2] = {{0,0},{3,7},{-5,19},{-1,-1},{INT64_MAX,1},{INT64_MIN,-1},{INT64_MIN,INT64_MAX},{INT64_MAX,INT64_MAX},{INT64_MIN,INT64_MIN},{INT64_C(4294967296),-7},{-7,INT64_C(4294967296)},{41,-80}};
        for (size_t i = 0; i < sizeof(fixed) / sizeof(fixed[0]); ++i) {
            const int64_t a=fixed[i][0],b=fixed[i][1];
            if (!check(a,b,signed_bits((uint64_t)a*2+(uint64_t)b*2+10))) return 1;
            ++count;
        }
        uint64_t state=UINT64_C(0x312fa56c70b981d4);
        for (size_t i=0;i<10000;++i) {
            state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); const int64_t a=signed_bits(state);
            state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); const int64_t b=signed_bits(state);
            if (!check(a,b,signed_bits((uint64_t)a*2+(uint64_t)b*2+10))) return 1;
            ++count;
        }
    }
    printf("stack cases passed: %zu\n",count); return 0;
}
