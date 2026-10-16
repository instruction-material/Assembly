#include "arithmetic.h"
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc != 2) { fputs("usage: arithmetic_fault_probe zero|overflow|negative\n", stderr); return 2; }
    if (strcmp(argv[1], "zero") == 0) printf("quotient=%" PRId64 "\n", unguarded_divide(7, 0));
    else if (strcmp(argv[1], "overflow") == 0) printf("quotient=%" PRId64 "\n", unguarded_divide(INT64_MIN, -1));
    else if (strcmp(argv[1], "negative") == 0) printf("quotient=%" PRId64 "\n", unguarded_divide(-21, 4));
    else { fputs("unknown probe case\n", stderr); return 2; }
    return 0;
}
