#ifndef ASSEMBLY_COMPILER_MODEL_H
#define ASSEMBLY_COMPILER_MODEL_H
#include <stdint.h>
int64_t compiled_score(int64_t value, int64_t factor, int64_t bias);
int preserved_compiled_ok(int64_t value, int64_t factor, int64_t bias);
#endif
