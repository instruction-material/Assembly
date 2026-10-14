#include "debug_lab.h"
#include <inttypes.h>
#include <stdio.h>
int main(void) {
    const int32_t values[] = {-8, -1, 4};
    const int64_t expected = 2;
    const int64_t observed = debug_first_nonnegative(values,
        (int64_t)(sizeof(values) / sizeof(values[0])));
    printf("observed=%" PRId64 " expected=%" PRId64 "\n", observed, expected);
    if (observed != expected) {
        fputs("known signed-comparison bug is still present\n", stderr);
        return 1;
    }
    return 0;
}
