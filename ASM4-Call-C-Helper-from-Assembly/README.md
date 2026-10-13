# ASM4 Call a C Helper from Assembly

Combine an array sum, a scale and a signed clamp across a real C/Assembly function call. The sum-and-scale loop is already present. The required learner task completes the helper invocation with correct argument mapping, stack alignment and preserved registers.

## Target and files

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, and GDB. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows.

Each role folder builds independently and contains `scale_and_clamp.S`, `main.c`, `helper.c`, `helper.h`, `tests.c`, `abi_checks.S` and `CMakeLists.txt`. Work in `starter/`; compare the separate `solution/` after testing a working attempt. Complete only `CALL_CLAMP` in `scale_and_clamp.S`. Keep the supplied helper and tests unchanged.

## Exact contract

```c
int64_t asm_scaled_clamped_sum(const int32_t *values, int64_t count,
                               int64_t scale, int64_t min_value,
                               int64_t max_value);
int64_t clamp_to_range(int64_t value, int64_t min_value, int64_t max_value);
```

- For `count <= 0`, the array is empty and is never read; a null array pointer is allowed.
- For positive count, the caller supplies at least that many readable signed 32-bit elements. Leave those elements unchanged.
- Sum sign-extended elements using the low 64 bits, then multiply by scale using the low 64 bits. Interpret that final bit pattern as signed before clamping.
- The caller supplies ordered signed bounds, `min_value <= max_value`.
- Invoke the actual C helper once for each assembly call, passing the scaled value and both bounds.
- The helper returns the lower bound for a value below it, the upper bound for a value above it, and the original value otherwise.
- Preserve RBX, RBP, R12 through R15, the stack pointer and return address.

The functions do not validate arbitrary array pointers or repair reversed bounds. These are caller preconditions. The C helper only compares signed values, so the wrapping sum and product are computed in assembly before the helper call.

## Five incoming arguments become three helper arguments

The assembly entry receives:

| Assembly input | Register |
| --- | --- |
| values | RDI |
| count | RSI |
| scale | RDX |
| min_value | RCX |
| max_value | R8 |

The existing loop uses R9 for its index, R10 for a sign-extended element, and RAX for the total. Its `imul` leaves the low 64-bit product in RAX.

The C helper then needs:

| Helper input | Register |
| --- | --- |
| scaled value | RDI |
| lower bound | RSI |
| upper bound | RDX |

Map the product and the still-live bounds into those registers before invoking the helper. Argument registers are caller-saved, so the helper may change them. Its return value arrives in RAX; keep that value as the assembly result.

## Stack alignment and preservation

For this ordinary integer System V call, the stack pointer at function entry has remainder 8 when divided by 16, because the caller's `call` pushed an eight-byte return address. Before the assembly routine issues another `call`, align RSP to a multiple of 16. The helper then observes an entry remainder of 8.

A balanced eight-byte stack adjustment or one saved-register push can establish that alignment. Restore every adjustment before returning. If a preserved register holds temporary state, save its incoming value and restore it. The reference uses a saved frame pointer; a completed learner may use a different balanced sequence.

The contract probe records the actual helper entry and forwards to the real C implementation. It checks invocation count, all three arguments and entry alignment. A separate shim seeds and checks all six callee-saved registers. Matching the numeric result without calling the helper is incomplete.

## Predict the example

The array `{4, -2, 9, 6, -1}` sums to 16:

| Scale | Low 64-bit product | Bounds | Returned clamp |
| --- | --- | --- | --- |
| 3 | 48 | -20 to 40 | 40 |
| 10 | 160 | -20 to 25 | 25 |

For an empty array, the sum and product are zero, but the helper still runs. Bounds 1 to 5 therefore produce 1. Negative scales and wide products need a signed interpretation of the final wrapped bit pattern before the clamp.

## Build, complete and test

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_helper
```

The untouched starter builds, but its missing helper invocation fails the contracts. The demo exits `78`, explains the incomplete or incorrect call on stderr, and prints no successful rows. A completed starter or reference prints:

```text
scaled and clamped=40
scaled and clamped=25
```

Build the reference with `-S solution -B build-solution`. Repeat completed roles in separate Release directories. For GCC, set both compiler options to `gcc`.

Each successful profile checks 11,280 array/scale/bound cases: empty and negative counts, signed extremes, negative and zero scales, products wider than 32 bits, equal bounds, full signed-range bounds, every prefix of fixed and deterministic arrays, unchanged input, actual helper arguments, entry alignment and preserved registers. Three input fixtures sit beside an unreadable guard page in read-only memory.

The test-only entry probe calls the same C clamp implementation under a different internal symbol. The ordinary demo links the production helper without that probe. The source and function signatures are the same across learner and reference roles.

## Debug the actual C boundary

```sh
gdb ./build-solution/assembly_helper
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *clamp_to_range
run
info registers rdi rsi rdx rsp
print ((unsigned long)$rsp & 15)
finish
print $rax
continue
```

The first helper entry receives 48, -20 and 40, its stack remainder is 8, and its return value is 40. The `*` breakpoint targets the first instruction, before the C prologue changes the stack pointer. For a longer trace, break at `asm_scaled_clamped_sum`, inspect its five argument registers, and step through the loop, multiplication, argument moves, call and balanced return.

## Completion evidence

1. Complete only the helper-call task and pass Debug and Release with Clang and GCC.
2. Record both default result rows, plus predicted cases below, inside and above the clamp interval.
3. Record an empty-array case whose bounds exclude zero and one full-width product.
4. Capture the actual C helper arguments, entry stack remainder and return value in GDB.
5. Explain caller-saved versus callee-saved registers, argument remapping and the effect of each push, call, pop or stack adjustment.

Independent study follows prediction, edit, test and trace. A guided session starts with the argument tables and a stack diagram, then examines the first failed contract. An optional extension can add a separately named helper and a new test set after the required ABI contract passes.

## References

- [System V x86-64 ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [GNU assembler Intel syntax](https://sourceware.org/binutils/docs/as/i386_002dVariations.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
