/**************************
*   CODING STANDARD   *
**************************/

// Use named constants, descriptive names, and purpose comments before nontrivial scopes

#include <stdint.h>

int64_t clamp_to_range(int64_t value, int64_t minValue, int64_t maxValue) {
	if (value < minValue)
		return minValue;
	if (value > maxValue)
		return maxValue;
	return value;
}
