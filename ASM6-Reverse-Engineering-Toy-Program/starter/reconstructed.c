#include <stdint.h>

int64_t student_reconstruction(int64_t value) {
	if (value < 0)
		value = -value;

	if ((value & 1) != 0)
		value = value * 3 + 1;
	else
		value = value / 2;

	return value;
}
