#include "array_routines.h"
#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>

int main(void) {
    const int32_t values[] = {12, -4, 7, 19, 3, 19, -8};
    const int64_t count = (int64_t)(sizeof(values) / sizeof(values[0]));
    const int64_t sum = asm_sum_array(values, count);
    const int64_t first10 = asm_find_first_ge(values, count, 10);
    const int64_t first18 = asm_find_first_ge(values, count, 18);
    const int64_t first20 = asm_find_first_ge(values, count, 20);
    if (sum != 48 || first10 != 0 || first18 != 3 || first20 != -1) {
        fputs("Array routine unfinished or incorrect; complete ARRAY_SEARCH and run the contracts.\n", stderr);
        return 78;
    }
    printf("sum=%" PRId64 "\nfirst >= 10=%" PRId64
           "\nfirst >= 18=%" PRId64 "\nfirst >= 20=%" PRId64 "\n",
           sum, first10, first18, first20);
    return 0;
}
