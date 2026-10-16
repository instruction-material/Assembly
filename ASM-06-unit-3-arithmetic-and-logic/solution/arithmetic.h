#ifndef ARITHMETIC_H
#define ARITHMETIC_H
#include <stddef.h>
#include <stdint.h>
enum ArithmeticOp { AR_ADD, AR_SUB, AR_MUL, AR_DIV, AR_AND, AR_OR, AR_XOR, AR_TEST, AR_CMP, AR_OP_COUNT };
enum { AR_CF = 1, AR_ZF = 64, AR_SF = 128, AR_OF = 2048, AR_ALL_FLAGS = 2241, AR_MUL_FLAGS = 2049 };
typedef struct { uint64_t value, auxiliary, flags, defined; } ArithmeticResult;
_Static_assert(sizeof(ArithmeticResult) == 32, "32-byte result required");
_Static_assert(offsetof(ArithmeticResult, auxiliary) == 8 && offsetof(ArithmeticResult, flags) == 16 && offsetof(ArithmeticResult, defined) == 24, "fixed field offsets required");
/* Linux x86-64 SysV: EDI op, RSI left, RDX right, RCX writable result.
   Return 1 and fill all fields. Reject null output, invalid op and unsafe
   signed division with 0 and no output write. Output must be valid storage.
   ADD/SUB/logic are modulo 2^64; MUL is signed full-width RDX:RAX;
   DIV is signed quotient/remainder. TEST/CMP preserve left in value.
   auxiliary is the product high word for MUL, remainder for DIV, zero otherwise.
   flags contains only defined CF/ZF/SF/OF bits selected by defined. */
int arithmetic_eval(uint32_t op, uint64_t left, uint64_t right, ArithmeticResult *out);
int arithmetic_model(uint32_t op, uint64_t left, uint64_t right, ArithmeticResult *out);
int preserved_registers_ok(uint32_t op, uint64_t left, uint64_t right, ArithmeticResult *out);
uint64_t arithmetic_c_mix(uint64_t left, uint64_t right);
int64_t unguarded_divide(int64_t left, int64_t right);
#endif
