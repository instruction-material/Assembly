/**************************
*   CODING STANDARD   *
**************************/

// Use named constants, descriptive names, and purpose comments before nontrivial scopes

#include <inttypes.h>
#include <stdio.h>

/****************
*   SOLUTION   *
****************/

int64_t asm_eval_expression(int64_t left, int64_t right, char op);

int main(void) {
	const struct {
		int64_t left;
		int64_t right;
		char op;
	} cases[] = {
		{ 12, 5, '+' },
		{ 12, 5, '-' },
		{ 7, 6, '*' },
		{ 21, 3, '/' },
		{ 0x2A, 0x0F, '&' },
		{ 0x2A, 0x0F, '^' }
	};

	const size_t caseCount = sizeof(cases) / sizeof(cases[0]);

	for (size_t index = 0; index < caseCount; index++) {
		const int64_t result =
			asm_eval_expression(cases[index].left, cases[index].right, cases[index].op);
		printf(
			"solution: %" PRId64 " %c %" PRId64 " => %" PRId64 "\n",
			cases[index].left,
			cases[index].op,
			cases[index].right,
			result
		);
	}

	return 0;
}
