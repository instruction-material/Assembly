#include "helper.h"
#include <inttypes.h>
#include <stdio.h>

int main(void) {
    const int32_t values[] = {4, -2, 9, 6, -1};
    const int64_t count = (int64_t)(sizeof(values) / sizeof(values[0]));
    const int64_t first = asm_scaled_clamped_sum(values, count, 3, -20, 40);
    const int64_t second = asm_scaled_clamped_sum(values, count, 10, -20, 25);
    if (first != 40 || second != 25) {
        fputs("Helper call unfinished or incorrect; complete CALL_CLAMP and run the contracts.\n", stderr);
        return 78;
    }
    printf("scaled and clamped=%" PRId64 "\nscaled and clamped=%" PRId64 "\n", first, second);
    return 0;
}
