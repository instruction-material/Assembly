/**************************
*   CODING STANDARD   *
**************************/

// Use named constants, descriptive names, and purpose comments before nontrivial scopes

#include <inttypes.h>
#include <stdio.h>

/****************
*   SOLUTION   *
****************/

int64_t asm_scaled_clamped_sum(
	const int32_t *values,
	int64_t count,
	int64_t scale,
	int64_t minValue,
	int64_t maxValue
);

int main(void) {
	const int32_t values[] = { 4, -2, 9, 6, -1 };
	const int64_t count = (int64_t)(sizeof(values) / sizeof(values[0]));

	printf(
		"solution scaled and clamped => %" PRId64 "\n",
		asm_scaled_clamped_sum(values, count, 3, -20, 40)
	);
	printf(
		"solution scaled and clamped => %" PRId64 "\n",
		asm_scaled_clamped_sum(values, count, 10, -20, 25)
	);

	return 0;
}
