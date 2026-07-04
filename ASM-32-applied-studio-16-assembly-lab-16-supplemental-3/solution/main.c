#include <stddef.h>
#include <stdio.h>

/*****************
*   CONSTANTS   *
*****************/

#define SAMPLE_VALUE_COUNT 4U


/*****************
*   FUNCTIONS   *
*****************/

/**
 * @brief Transform one value using the assembly routine
 *
 * @param value Value to transform
 *
 * @return Transformed value
 */
extern int transform_value(int value);

/**
 * @brief Print the total for the transformed sample values
 *
 * @return Program exit status
 */
int main(void) {
	const int values[SAMPLE_VALUE_COUNT] = {3, 7, 11, 19};
	int total = 0;

	// Transform each input value and accumulate the total
	for (size_t value_index = 0U; value_index < SAMPLE_VALUE_COUNT; value_index++) {
		total += transform_value(values[value_index]);
	}

	printf("total=%d\n", total);
	return 0;
}
