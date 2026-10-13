#include "string_routines.h"
#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    char wide[16] = {0};
    char small[6] = {0};
    const char *source = "assembly";
    const uint64_t length = asm_strlen_simple("registers");
    const uint64_t wide_length = asm_strlcpy_simple(wide, source, sizeof(wide));
    const uint64_t small_length = asm_strlcpy_simple(small, source, sizeof(small));
    const uint64_t zero_length = asm_strlcpy_simple(NULL, source, 0);
    if (length != 9 || wide_length != 8 || small_length != 8 || zero_length != 8 ||
        strcmp(wide, "assembly") || strcmp(small, "assem")) {
        fputs("String routine unfinished or incorrect; complete COPY_SOURCE_LENGTH and run the contracts.\n", stderr);
        return 78;
    }
    printf("strlen=%" PRIu64 "\nwide length=%" PRIu64 " text=%s\n"
           "small length=%" PRIu64 " text=%s\nzero capacity length=%" PRIu64 "\n",
           length, wide_length, wide, small_length, small, zero_length);
    return 0;
}
