/**************************
*   CODING STANDARD   *
**************************/

// Use named constants, descriptive names, and purpose comments before nontrivial scopes

#include <stdint.h>

int64_t student_reconstruction(int64_t value) {
	if (value < 0)
		value = -value;

	if ((value & 1) != 0)
		value = value * 3 + 1;
	else
		value = value / 2;

	if (value > 40)
		value += 7;
	else
		value -= 5;

	return value;
}
