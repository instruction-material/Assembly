/**************************
*   CODING STANDARD   *
**************************/

// Use named constants, descriptive names, and purpose comments before nontrivial scopes

#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>

/****************
*   SOLUTION   *
****************/

int64_t asm_sum_array(const int32_t *values, int64_t count);
int64_t asm_find_first_ge(const int32_t *values, int64_t count, int32_t threshold);

int main(void) {
	const int32_t values[] = { 12, -4, 7, 19, 3, 19, -8 };
	const int64_t count = (int64_t)(sizeof(values) / sizeof(values[0]));

	printf("solution sum => %" PRId64 "\n", asm_sum_array(values, count));
	printf(
		"solution first >= 10 => %" PRId64 "\n",
		asm_find_first_ge(values, count, 10)
	);
	printf(
		"solution first >= 20 => %" PRId64 "\n",
		asm_find_first_ge(values, count, 20)
	);

	return 0;
}
