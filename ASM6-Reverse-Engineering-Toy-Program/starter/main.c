#include "reverse.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

static int ready(void) {
    const int64_t inputs[] = {-9, -4, 7, 18, 32, 41, 0, 13, 15, 80, 82, INT64_MIN, INT64_MAX};
    for (size_t i = 0; i < sizeof(inputs) / sizeof(inputs[0]); ++i)
        if (student_reconstruction(inputs[i]) != mystery_score(inputs[i])) return 0;
    return 1;
}
static int parse(const char *text, int64_t *out) {
    size_t i = (text[0] == '+' || text[0] == '-') ? 1 : 0;
    if (text[i] == 0) return 0;
    for (; text[i] != 0; ++i) if (text[i] < '0' || text[i] > '9') return 0;
    errno = 0;
    char *end = NULL;
    const intmax_t value = strtoimax(text, &end, 10);
    if (errno == ERANGE || *end || value < INT64_MIN || value > INT64_MAX) return 0;
    *out = (int64_t)value;
    return 1;
}
static int show(int64_t input) {
    const int64_t original = mystery_score(input);
    const int64_t reconstructed = student_reconstruction(input);
    if (original != reconstructed) { fputs("Reconstruction differs on the requested input.\n", stderr); return 0; }
    printf("input=%" PRId64 " mystery=%" PRId64 " reconstructed=%" PRId64 "\n",
           input, original, reconstructed);
    return 1;
}
int main(int argc, char **argv) {
    if (argc > 2) { fputs("Supply zero or one signed decimal 64-bit input.\n", stderr); return 2; }
    int64_t input = 0;
    if (argc == 2 && !parse(argv[1], &input)) {
        fputs("Supply zero or one signed decimal 64-bit input.\n", stderr); return 2;
    }
    if (!ready()) {
        fputs("Reconstruction unfinished or incorrect; complete RECONSTRUCT_THRESHOLD and run the contracts.\n", stderr);
        return 78;
    }
    if (argc == 2) return show(input) ? 0 : 78;
    const int64_t values[] = {-9, -4, 7, 18, 32, 41};
    for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i)
        if (!show(values[i])) return 78;
    return 0;
}
