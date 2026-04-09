#include <inttypes.h>
#include <stdio.h>

int64_t mystery_score(int64_t value);
int64_t student_reconstruction(int64_t value);

int main(void) {
	const int64_t values[] = { -9, -4, 7, 18, 32, 41 };
	const size_t count = sizeof(values) / sizeof(values[0]);

	for (size_t index = 0; index < count; index++) {
		const int64_t original = mystery_score(values[index]);
		const int64_t guess = student_reconstruction(values[index]);
		printf(
			"starter input=%" PRId64 " mystery=%" PRId64 " guess=%" PRId64 "\n",
			values[index],
			original,
			guess
		);
	}

	return 0;
}
