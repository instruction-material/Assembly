#include "lab.h"
int compiled_signed_compare(int8_t value, int threshold) {
    return value < threshold;
}
int compiled_unsigned_compare(uint8_t value, int threshold) {
    return value < threshold;
}
