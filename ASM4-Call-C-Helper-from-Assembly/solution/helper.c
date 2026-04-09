#include <stdint.h>

int64_t clamp_to_range(int64_t value, int64_t minValue, int64_t maxValue) {
	if (value < minValue)
		return minValue;
	if (value > maxValue)
		return maxValue;
	return value;
}
