# ASM2 Array Sum and Search

Build and trace bounded array loops in Linux x86-64 assembly. The summation routine is complete; the learner implements the first-threshold search. This project applies the register and arithmetic work to scaled memory addressing and signed branches.

## Target and tools

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, and GDB. The `.S` suffix enables preprocessing before assembly. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows. The role folders build independently after download.

## Files and learning task

Each role has `array_routines.S`, `array_routines.h`, `main.c`, `tests.c`, `abi_checks.S`, and `CMakeLists.txt`. `starter/` preserves the complete sum implementation and has one `ARRAY_SEARCH` task. `solution/` is the reference. Work in the starter and compare the reference after recording a working attempt.

Edit only the `asm_find_first_ge` body in `array_routines.S` for the required task. Keep the function signatures, test driver, and tests intact. Annotate the counter, current address, comparison and next branch in a separate trace table.

## Exact function contract

```c
int64_t asm_sum_array(const int32_t *values, int64_t count);
int64_t asm_find_first_ge(const int32_t *values, int64_t count,
                          int32_t threshold);
```

- For `count <= 0`, sum returns `0` and search returns `-1`, without reading `values`. A null pointer is allowed only in this empty-input case.
- For `count > 0`, the caller supplies at least `count` readable `int32_t` elements. The routines never write those elements and never read `values[count]`.
- Sum sign-extends each 32-bit element and returns the signed interpretation of the low 64 bits of the total.
- Search compares signed 32-bit values and returns the first zero-based index whose value is greater than or equal to the threshold. Return `-1` when no element matches.
- Preserve RBX, RBP and R12 through R15, the stack pointer and the caller's return address.

These functions do not validate arbitrary pointer addresses. The caller establishes the readable array bound. Empty input is handled before any memory access.

## Registers and addressing

The sum receives `values` in RDI and `count` in RSI. Search also receives `threshold` in EDX. Return the result in RAX. RCX and R8 are available as caller-saved loop state. An element address is `values + index * 4`, because each `int32_t` occupies four bytes. A 32-bit load for a signed sum needs sign extension into the 64-bit accumulator.

For search, compare the value and threshold as signed values. Operand order changes which conditional jump expresses the desired comparison. Check `index < count` before loading, and return immediately on the first match. A later matching element must not replace an earlier result.

## Build and run

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_array
```

Before completion, the starter builds but its contracts fail. The demo exits `78`, reports that the routine is unfinished or incorrect on stderr, and prints no successful result rows. After a correct search implementation, the same commands pass and the demo prints:

```text
sum=48
first >= 10=0
first >= 18=3
first >= 20=-1
```

Build the reference with `-S solution -B build-solution`. For GCC, set both compiler options to `gcc`. Repeat the completed starter and reference with `-DCMAKE_BUILD_TYPE=Release` in separate build folders.

## Worked trace

Use `{12, -4, 7, 19, 3, 19, -8}` and threshold `18`:

| Index | Value | Comparison | Next action |
| --- | --- | --- | --- |
| 0 | 12 | 12 < 18 | advance to 1 |
| 1 | -4 | -4 < 18 | advance to 2 |
| 2 | 7 | 7 < 18 | advance to 3 |
| 3 | 19 | 19 >= 18 | return 3 |

The later `19` at index 5 does not change the first-match answer. For a threshold of 20, every element fails and the loop returns `-1` after checking the bound. The running sums are `12, 8, 15, 34, 37, 56, 48`.

## Instruction-level debugger pass

```sh
gdb ./build-solution/assembly_array
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak asm_find_first_ge
run
info registers rdi rsi edx rcx rax
x/7wd $rdi
disassemble asm_find_first_ge
si
finish
print $rax
continue
```

The first search receives count 7 and threshold 10 and returns 0. For a detailed loop trace, step through the search with `si`, recording RCX, the element address, the loaded value, the flags after `cmp`, and the selected branch. Explain why a negative element compares correctly and why the bound check occurs before the load.

## Completion evidence

Run the unchanged contracts. Each successful profile checks 11,280 array/threshold cases: empty and negative counts with a null pointer, every prefix of fixed arrays, signed extremes, repeated matches, missing matches, deterministic wider inputs, six preserved registers for both calls, and protected input adjacent to an unreadable guard page.

The protected input checks reject a write or an extra read in that fixture. Other fixtures verify that every readable element remains unchanged. These tests establish the stated cases and machine contract; they do not make invalid caller pointers valid.

Record:

1. A completed starter that passes Debug and Release with Clang and GCC.
2. The four expected demo rows and a first-match trace.
3. A custom array with negative values, two qualifying elements, and a no-match threshold; predict sum and index before running.
4. An explanation of signed versus unsigned comparisons, sign extension, the four-byte scale, and the first-match exit.
5. A debugger observation that matches the source-level prediction.

For an instructor-guided session, first predict the fixed trace together, then have the learner implement the search and explain the first failing case. For independent study, use the same prediction, edit, test and trace sequence. An optional extension can add a last-match routine under a new name and new tests after the required contract passes.

## References

- [System V x86-64 ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [GNU assembler Intel syntax](https://sourceware.org/binutils/docs/as/i386_002dVariations.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
