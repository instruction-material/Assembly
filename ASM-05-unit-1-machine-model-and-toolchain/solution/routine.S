/*****************
*   CONSTANTS   *
*****************/

#define TRANSFORM_OFFSET 5


/*****************
*   FUNCTIONS   *
*****************/

#ifdef __APPLE__
.global _transform_value
// Transform input by doubling it and adding the lesson offset
_transform_value:
#else
.global transform_value
// Transform input by doubling it and adding the lesson offset
transform_value:
#endif
	leal TRANSFORM_OFFSET(%rdi,%rdi), %eax
	ret
