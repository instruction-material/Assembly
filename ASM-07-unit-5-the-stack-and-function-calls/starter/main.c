#include "stack.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static int64_t model(int64_t a, int64_t b) {
    const uint64_t bits = (uint64_t)a * 2 + (uint64_t)b * 2 + 10;
    int64_t result; memcpy(&result, &bits, sizeof(result)); return result;
}
int main(void) {
    const int64_t pairs[][2] = {{3,7},{-5,19},{INT64_MAX,1},{INT64_MIN,-1}};
    for (size_t i = 0; i < sizeof(pairs) / sizeof(pairs[0]); ++i)
        if (stack_pair(pairs[i][0],pairs[i][1]) != model(pairs[i][0],pairs[i][1])) {
            fputs("Stack-call task unfinished or incorrect; complete STACK_CALLS and run the contracts.\n",stderr);
            return 78;
        }
    for (size_t i = 0; i < sizeof(pairs) / sizeof(pairs[0]); ++i)
        printf("a=%" PRId64 " b=%" PRId64 " result=%" PRId64 "\n",pairs[i][0],pairs[i][1],stack_pair(pairs[i][0],pairs[i][1]));
    return 0;
}
