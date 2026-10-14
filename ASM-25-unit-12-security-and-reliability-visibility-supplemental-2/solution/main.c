#include "hardening.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strlen(argv[1]) > 32)) {
        fputs("usage: assembly_hardening [text-with-at-most-32-bytes]\n", stderr);
        return 2;
    }
    const char *text = argc == 2 ? argv[1] : "Assembly";
    const size_t count = strlen(text);
    const uint64_t c = checksum_c((const uint8_t *)text, (int64_t)count);
    const uint64_t assembly = checksum_asm((const uint8_t *)text, (int64_t)count);
    printf("count=%zu c=%" PRIu64 " asm=%" PRIu64 " match=%s\n",
           count, c, assembly, c == assembly ? "yes" : "no");
    return c == assembly ? 0 : 1;
}
