#ifndef STRING_ROUTINES_H
#define STRING_ROUTINES_H
#include <stdint.h>

/* text/src are readable through a terminating NUL byte.
   src and dest do not overlap. If capacity > 0, dest has capacity writable bytes.
   If capacity == 0, dest is never accessed and may be NULL.
   Copy writes at most capacity-1 data bytes plus one NUL when capacity > 0,
   and returns the full source byte length, excluding NUL.
   Both routines preserve the input and System V callee-saved registers. */
uint64_t asm_strlen_simple(const char *text);
uint64_t asm_strlcpy_simple(char *dest, const char *src, uint64_t capacity);
#endif
