#include "transform.h"
#include <inttypes.h>
#include <stdio.h>

int main(void) {
    if (transform_value(0) != 5 || transform_value(-1) != 3 ||
        transform_value(3) != 11) {
        fputs("Assembly transform task is unfinished or incorrect.\n", stderr);
        return 78;
    }
    const int32_t values[] = {3, 7, 11, 19};
    int64_t total = 0;
    for (size_t i = 0; i < sizeof values / sizeof values[0]; ++i)
        total += transform_value(values[i]);
    printf("total=%" PRId64 "\n", total);
    return 0;
}
