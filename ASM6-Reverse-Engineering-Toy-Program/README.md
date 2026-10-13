# ASM6 Reverse-Engineering Toy Program

Recover equivalent pseudocode and C from a supplied assembly routine, then test the reconstruction against the original. This is a reverse-trace project: the assembly algorithm stays intact and the required learner edit is in C. The final branch is missing from the starter reconstruction.

## Target, tools and roles

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, GDB and objdump. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows. Each role folder builds independently and contains `mystery.S`, `reconstructed.c`, `reverse.h`, `main.c`, `tests.c`, `abi_checks.S` and `CMakeLists.txt`.

Start by disassembling `mystery_score` and recording pseudocode for its three phases. Complete only `RECONSTRUCT_THRESHOLD` in `starter/reconstructed.c`. Keep the supplied assembly, tests and function signatures unchanged. Save a working attempt before comparing the separate reference.

## Exact behavior across the full input range

Both functions accept and return `int64_t`; every input from `INT64_MIN` through `INT64_MAX` is valid. The assembly operates on 64-bit two's-complement bit patterns. Its NEG, LEA, ADD and SUB results retain the low 64 bits. Its final comparison is signed.

1. Copy the input. For a negative input, negate its bits modulo 2^64. For `INT64_MIN`, the bits remain unchanged; this is not a representable positive signed absolute value.
2. An odd bit pattern becomes the low 64 bits of three times that pattern plus one. An even pattern takes an arithmetic right shift by one bit, preserving its sign bit. Only the minimum input remains negative after the first phase. Its SAR result is -4611686018427387904.
3. Interpret the intermediate bits as signed. A value strictly greater than 40 gains seven modulo 2^64. Every other value loses five modulo 2^64. Interpret the final bits as signed for the return value.

RDI carries the input and RAX the result. Preserve RBX, RBP and R12 through R15, the stack pointer and return address. There are no input pointers or memory writes in the mystery routine.

## Reconstruct without C signed overflow

The supplied C prefix uses `uint64_t` for modular arithmetic and `memcpy` to interpret the final bit representation as `int64_t`. Unsigned negation and multiplication are defined modulo 2^64. `(bits >> 1) | (bits & (UINT64_C(1) << 63))` reproduces the one-bit arithmetic shift without relying on C's treatment of a signed right shift.

For the missing phase, make the signed comparison using `signed_bits(bits)`, then apply the appropriate unsigned offset and return `signed_bits` of the final bits. Keep the intermediate in unsigned storage. Ordinary signed `-value`, `value * 3 + 1` and final additions can overflow on valid inputs and are not faithful reconstructions. The build enables undefined-behavior sanitization for C in Debug and Release; tests still check numeric equivalence independently.

## Prediction table

| Input | After negation phase | After parity phase | Final branch | Return |
| --- | --- | --- | --- | --- |
| -9 | 9 | 28 | 28 <= 40 | 23 |
| -4 | 4 | 2 | 2 <= 40 | -3 |
| 7 | 7 | 22 | 22 <= 40 | 17 |
| 18 | 18 | 9 | 9 <= 40 | 4 |
| 32 | 32 | 16 | 16 <= 40 | 11 |
| 41 | 41 | 124 | 124 > 40 | 131 |
| 13 | 13 | 40 | equality takes the lower path | 35 |
| 82 | 82 | 41 | 41 > 40 | 48 |
| INT64_MIN | INT64_MIN bits | -4611686018427387904 | lower path | -4611686018427387909 |
| INT64_MAX | INT64_MAX | 9223372036854775806 | upper path wraps | -9223372036854775803 |

Predict the boundary rows before running. The comparison occurs after the parity phase, so comparing the original input to 40 is incorrect. Flags from NEG do not determine that final branch; CMP sets the flags used by JG.

## Build and complete

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_reverse
```

The untouched starter builds, fails its contracts and exits 78 without successful result rows. After completing the C reconstruction, the demo prints the six ordinary-input comparisons in the prediction table and exits zero. Each row includes `input`, `mystery` and `reconstructed`; the two results must match.

Build the reference with `-S solution -B build-solution`. Repeat in separate Release folders and with both compiler options set to `gcc`. Keep sanitization enabled. A clean build is only the first gate; require CTest, demo and changed cases to succeed.

One signed decimal operand requests a changed case:

```sh
./build-solution/assembly_reverse 13
./build-solution/assembly_reverse -9223372036854775808
./build-solution/assembly_reverse 9223372036854775807
```

The expected returns are 35, -4611686018427387909 and -9223372036854775803. Invalid text, out-of-range input or more than one operand exits 2, reports on stderr and prints no result rows, including in an untouched starter.

## Observe the compiled routine

```sh
objdump -d -M intel build-solution/assembly_reverse
gdb ./build-solution/assembly_reverse
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *mystery_score
run
info registers rdi rax rip rsp
disassemble mystery_score
si
finish
print $rax
continue
```

The first readiness call receives -9 and returns 23. Stepping through it shows negation to 9, the odd LEA result 28, the signed comparison against 40 and subtraction of five. Repeat with 13 to see equality take the lower path and with the minimum input to examine the unchanged NEG bits and SAR sign extension. Record actual instruction addresses and branch choices; addresses depend on the build.

## Completion evidence and extension

1. Record pseudocode for all three phases, with the signed comparison, modulo arithmetic and minimum-input exception explicit.
2. Complete only the missing reconstruction task and pass Debug and Release with both compilers.
3. Record the six demo comparisons and changed cases on both sides of the threshold, at equality and at both signed extremes.
4. Trace the original routine in GDB and explain the flags used by each branch.
5. Explain why matching the six ordinary examples alone cannot establish full-range equivalence.

Each successful native profile checks 10,033 fixed and deterministic full-width inputs against both functions and six preserved registers per function. A separate arbitrary-precision Python oracle supplies the same inputs with independently calculated expected results. Controlled regressions check threshold equality, signed comparison, offsets, arithmetic shift, C undefined overflow and register preservation. These checks support the stated input cases; they do not claim exhaustive enumeration of all 2^64 inputs.

Independent study follows disassembly, prediction, pseudocode, edit, test and trace. A guided session starts with a control-flow sketch and examines the first mismatching case. An optional extension can change the assembly threshold or offsets in a separate copy and recover its behavior with a new independent model after the original contract passes.

## References

- [Intel instruction-set manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [GNU objdump options](https://sourceware.org/binutils/docs/binutils/objdump.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
- [GCC undefined-behavior instrumentation](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
