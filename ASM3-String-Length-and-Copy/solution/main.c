#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>

uint64_t asm_strlen_simple(const char *text);
uint64_t asm_strlcpy_simple(char *dest, const char *src, uint64_t capacity);

int main(void) {
	char wideBuffer[16] = { 0 };
	char smallBuffer[6] = { 0 };
	const char *source = "assembly";

	printf("solution strlen(registers) => %" PRIu64 "\n", asm_strlen_simple("registers"));
	printf(
		"solution copied wide => %" PRIu64 ", \"%s\"\n",
		asm_strlcpy_simple(wideBuffer, source, sizeof(wideBuffer)),
		wideBuffer
	);
	printf(
		"solution copied small => %" PRIu64 ", \"%s\"\n",
		asm_strlcpy_simple(smallBuffer, source, sizeof(smallBuffer)),
		smallBuffer
	);

	return 0;
}
