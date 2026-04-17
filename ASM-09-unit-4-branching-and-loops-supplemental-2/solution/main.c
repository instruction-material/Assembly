#include <stdio.h>

extern int transform_value(int value);

int main(void) {
	int values[] = {3, 7, 11, 19};
	int total = 0;
	for (int i = 0; i < 4; i++) {
		total += transform_value(values[i]);
	}
	printf("total=%d\n", total);
	return 0;
}
