#include "lab.h"
uint64_t compiled_plain(uint64_t *left, uint64_t *right, uint64_t delta) {
    *left += delta;
    *right ^= *left;
    return *left;
}
uint64_t compiled_restricted(uint64_t *restrict left, uint64_t *restrict right, uint64_t delta) {
    *left += delta;
    *right ^= *left;
    return *left;
}
