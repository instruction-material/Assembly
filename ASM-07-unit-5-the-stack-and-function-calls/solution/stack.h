#ifndef ASSEMBLY_STACK_H
#define ASSEMBLY_STACK_H
#include <stdint.h>
int64_t stack_pair(int64_t a, int64_t b);
int64_t stack_leaf(int64_t input);
int preserved_stack_ok(int64_t a, int64_t b);
#endif
