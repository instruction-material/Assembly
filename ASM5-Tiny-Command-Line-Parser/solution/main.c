#include <inttypes.h>
#include <stdio.h>

/****************
*   SOLUTION   *
****************/

int asm_streq(const char *left, const char *right);
int asm_parse_i64(const char *text, int64_t *outValue);

int main(int argc, char **argv) {
	if (argc < 4) {
		printf("usage: <sum|max|xor> <n1> <n2> [n3 ...]\n");
		return 0;
	}

	int64_t result = 0;
	int firstValue = 1;

	for (int index = 2; index < argc; index++) {
		int64_t parsed = 0;
		if (!asm_parse_i64(argv[index], &parsed)) {
			printf("solution parse error: %s\n", argv[index]);
			return 0;
		}

		if (asm_streq(argv[1], "sum")) {
			result += parsed;
		}
		else if (asm_streq(argv[1], "max")) {
			if (firstValue || parsed > result)
				result = parsed;
		}
		else if (asm_streq(argv[1], "xor")) {
			if (firstValue)
				result = parsed;
			else
				result ^= parsed;
		}
		else {
			printf("solution unknown command: %s\n", argv[1]);
			return 0;
		}

		firstValue = 0;
	}

	printf("solution %s => %" PRId64 "\n", argv[1], result);
	return 0;
}
