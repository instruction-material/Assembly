#include "lab.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed"))) {
        fputs("Use no argument or --changed.\n", stderr); return 64;
    }
    const uint64_t initial = argc == 2 ? UINT64_C(0) : UINT64_C(0x8007);
    const uint64_t incoming = argc == 2 ? UINT64_C(0) : UINT64_C(0x80ff7f0100fe0281);
    LabResult actual = {0}, expected = {0};
    lab_operation(initial, incoming, &actual); lab_model(initial, incoming, &expected);
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field)
        if (actual.value[field] != expected.value[field]) {
            fprintf(stderr, "Compiler observation mismatch: field=%zu\n", field); return 78;
        }
    printf("initial=%016" PRIx64 " incoming=%016" PRIx64 "\n", initial, incoming);
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field)
        printf("%s=%016" PRIx64 "\n", lab_field_names[field], actual.value[field]);
    return 0;
}
