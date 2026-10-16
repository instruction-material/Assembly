#include "lab.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed"))) {
        fputs("Use no argument or --changed.\n", stderr);
        return 64;
    }
    const int changed = argc == 2;
    const uint64_t initial = changed ? UINT64_C(0xffeeddccbbaa0099) : UINT64_C(0x1122334455667788);
    const uint64_t incoming = changed ? UINT64_C(0xfedcba987fff7f80) : UINT64_C(0x11223344800080ff);
    LabResult actual = {0}, expected = {0};
    lab_model(initial, incoming, &expected);
    lab_operation(initial, incoming, &actual);
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field) {
        if (actual.value[field] != expected.value[field]) {
            fprintf(stderr, "Incomplete width contract: field=%zu actual=%016" PRIx64 " expected=%016" PRIx64 "\n", field, actual.value[field], expected.value[field]);
            return 78;
        }
    }
    printf("initial=%016" PRIx64 " incoming=%016" PRIx64 "\n", initial, incoming);
    for (size_t field = 0; field < LAB_FIELD_COUNT; ++field)
        printf("%s=%016" PRIx64 "\n", lab_field_names[field], actual.value[field]);
    return 0;
}
