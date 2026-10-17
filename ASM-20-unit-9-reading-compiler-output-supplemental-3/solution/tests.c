#include "lab.h"
#include <inttypes.h>
#include <ctype.h>
#include <stdio.h>
#include <string.h>
static int read_hex_word(uint64_t *output) {
    int ch;
    do { ch = getchar(); } while (ch != EOF && isspace((unsigned char)ch));
    if (ch == EOF) return ferror(stdin) ? -1 : 0;
    uint64_t value = 0;
    unsigned digits = 0;
    while (ch != EOF && !isspace((unsigned char)ch)) {
        int digit;
        if (ch >= '0' && ch <= '9') digit = ch - '0';
        else if (ch >= 'a' && ch <= 'f') digit = ch - 'a' + 10;
        else if (ch >= 'A' && ch <= 'F') digit = ch - 'A' + 10;
        else return -1;
        if (digits == 16) return -1;
        value = (value << 4U) | (uint64_t)digit;
        ++digits;
        ch = getchar();
    }
    if (ch == EOF && ferror(stdin)) return -1;
    *output = value;
    return 1;
}

static int check(uint64_t initial, uint64_t incoming) {
    LabResult actual = {0}, expected = {0};
    int preserved = 0;
    lab_model(initial, incoming, &expected);
    abi_probe(lab_operation, initial, incoming, &actual, &preserved);
    if (!preserved) { fputs("ABI preservation failed\n", stderr); return 1; }
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field) {
        if (actual.value[field] != expected.value[field]) {
            fprintf(stderr, "Mismatch initial=%016" PRIx64 " incoming=%016" PRIx64 " field=%zu actual=%016" PRIx64 " expected=%016" PRIx64 "\n", initial, incoming, field, actual.value[field], expected.value[field]);
            return 1;
        }
    }
    return 0;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--rows")) {
        for (;;) {
            uint64_t initial = 0, incoming = 0;
            const int first = read_hex_word(&initial);
            if (first == 0) return 0;
            if (first < 0 || read_hex_word(&incoming) != 1) return 64;
            LabResult actual = {0}; int preserved = 0;
            abi_probe(lab_operation, initial, incoming, &actual, &preserved);
            printf("%d", preserved);
            for (size_t field = 0; field < LAB_FIELD_COUNT; ++field) printf(" %016" PRIx64, actual.value[field]);
            putchar('\n');
        }
    }
    if (argc != 1) return 64;
    const uint64_t fixed[] = {0,1,2,31,32,63,64,65,127,128,255,UINT64_C(0x7fffffffffffffff),UINT64_C(0x8000000000000000),UINT64_C(0x8000000000000001),UINT64_C(0xaaaaaaaaaaaaaaaa),UINT64_MAX};
    size_t count = 0;
    for (size_t i = 0; i < sizeof(fixed)/sizeof(fixed[0]); ++i)
        for (size_t j = 0; j < sizeof(fixed)/sizeof(fixed[0]); ++j) {
            if (check(fixed[i], fixed[j])) return 1;
            ++count;
        }
    uint64_t state = UINT64_C(0xdecafbad87912345);
    for (size_t i = 0; i < 10013; ++i) {
        state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        const uint64_t initial = state;
        state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
        if (check(initial, state)) return 1;
        ++count;
    }
    printf("compiler observation contracts passed: %zu\n", count);
    return 0;
}
