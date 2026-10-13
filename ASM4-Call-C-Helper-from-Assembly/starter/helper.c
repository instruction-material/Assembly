#include "helper.h"

/* Contract builds place an entry probe before the actual C implementation. */
#ifdef ASSEMBLY_HELPER_PROBE
#define clamp_to_range clamp_implementation
#endif

int64_t clamp_to_range(int64_t value, int64_t min_value, int64_t max_value) {
    if (value < min_value) return min_value;
    if (value > max_value) return max_value;
    return value;
}
