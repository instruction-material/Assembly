#include "model.h"
#include <string.h>

int64_t compiled_score(int64_t value, int64_t factor, int64_t bias) {
    const uint64_t bits = (uint64_t)value * (uint64_t)factor + (uint64_t)bias;
    int64_t result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}
