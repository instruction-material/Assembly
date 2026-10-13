# ASM5 Tiny Command-Line Parser

Parse signed decimal text and dispatch `sum`, `max` or `xor` in a mixed C/Assembly program. The learner completes optional-sign handling and the magnitude-bound check in the existing digit loop.

## Target and files

Use Linux x86-64, the System V AMD64 ABI, GNU/Clang Intel syntax, CMake 3.20 or later, Clang or GCC, and GDB. Use an x86-64 Linux VM or lab on macOS, or an x86-64 WSL distribution on Windows.

Each independent role folder has `parser.S`, `parser.h`, `main.c`, `tests.c`, `abi_checks.S` and `CMakeLists.txt`. Work in `starter/`. Complete only `PARSE_SIGN` and `PARSE_BOUND` in `parser.S`; the equality routine, digit loop, caller and tests are supplied. Review the separate reference after a working attempt.

## Exact function contract

```c
int asm_streq(const char *left, const char *right);
int asm_parse_i64(const char *text, int64_t *out_value);
```

String inputs are readable through a zero terminator. The output points to one writable `int64_t`. The routines leave input bytes unchanged and preserve RBX, RBP and R12 through R15, the stack pointer and return address.

Equality is byte-for-byte and case-sensitive, returning exactly `1` or `0`. Parsing accepts an optional initial `+` or `-`, followed by at least one ASCII digit, then the zero terminator. Leading zeroes and signed zero are allowed.

Parsing succeeds only for values from `-9223372036854775808` through `9223372036854775807`. Success stores one signed value and returns `1`. Invalid syntax or range returns `0` without changing the output slot. Empty text, a sign alone, whitespace, extra signs, hexadecimal notation, decimal points, trailing characters and oversized values are rejected.

## Registers and parse state

Equality receives its two pointers in RDI and RSI. Parsing receives the text pointer in RDI and output pointer in RSI; its success flag returns in EAX. The supplied parser keeps the output pointer in R8, index in RCX, magnitude in RAX, negative flag in R9D, quotient bound in R10 and final allowed digit in R11D.

For `PARSE_SIGN`, advance past an initial sign, mark a negative sign and choose final digit 8 for negative input or 7 otherwise. Reject a sign with no following digit. For `PARSE_BOUND`, check the next magnitude before the multiply/add.

The maximum permitted magnitude is `9223372036854775807` for positive input and `9223372036854775808` for negative input. Both share quotient `922337203685477580` when divided by 10. Before accepting a digit:

1. Reject a current magnitude larger than that quotient.
2. When equal to the quotient, reject a next digit above 7 for positive input or 8 for negative input.
3. Otherwise multiply the magnitude by 10 and add the digit.

Use unsigned magnitude comparisons. Apply a negative sign only after the entire input is valid, then store the result. The negative minimum has a magnitude one larger than the positive maximum; it must remain accepted. Storing only on success preserves the caller's earlier output when parsing fails.

## Predict boundary cases

| Text | Success | Stored value |
| --- | --- | --- |
| +00042 | 1 | 42 |
| -0 | 1 | 0 |
| 9223372036854775807 | 1 | positive maximum |
| -9223372036854775808 | 1 | negative minimum |
| 9223372036854775808 | 0 | previous output unchanged |
| -9223372036854775809 | 0 | previous output unchanged |
| + or 12x | 0 | previous output unchanged |

Trace the final digit of both limits. Record the index, digit, magnitude before the update, bound comparison, next branch and output-write decision.

## Command-line behavior

Commands are case-sensitive and require at least two operands. The caller checks command, arity, syntax and range before accepting a learner parser result. Invalid user input exits `2`, prints an explanation on stderr and prints no result. An unfinished or incorrect parser exits `78` without successful result rows.

`sum` uses low 64-bit wrapping addition, implemented through unsigned C arithmetic before interpreting the final bit pattern as signed. `max` uses signed comparisons. `xor` combines the 64-bit operand bit patterns. This defines boundary behavior without signed C addition overflow.

After completion:

```sh
./build/assembly_parser sum 12 -4 7
./build/assembly_parser max 12 -4 7
./build/assembly_parser xor 12 -4 7
./build/assembly_parser sum 9223372036854775807 1
./build/assembly_parser max -5 -9
```

These print `result=15`, `result=12`, `result=-9`, `result=-9223372036854775808` and `result=-5`, each on its own line with exit zero. An example rejection is:

```sh
./build/assembly_parser sum 9223372036854775808 0
```

With no arguments, the completed demo parses its fixed operands and computes:

```text
sum=15
max=12
xor=-9
```

## Build and completion checks

From the project folder:

```sh
cmake -S starter -B build-starter -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DCMAKE_ASM_COMPILER=clang
cmake --build build-starter
ctest --test-dir build-starter --output-on-failure
./build-starter/assembly_parser
```

The untouched starter builds but fails its contracts and demo. Build the reference with `-S solution -B build-solution`. Repeat completed roles in separate Release folders and with both compiler options set to `gcc`.

Each successful profile checks 8,056 parse cases and 1,101 equality cases, including both signed limits, oversized decimals, leading zeroes, signed zero, malformed text, deterministic full-width values, exact success flags, unchanged failed-output slots and preserved registers. Protected fixtures put each input terminator and the eight-byte output beside unreadable pages and keep input memory read-only.

Separate command-line checks verify all three commands, negative maxima, wide/wrapping sums, invalid command and arity, malformed later operands, stderr/no-result behavior and exact exit statuses. Checks remain active in Release builds.

## Debug the first parse

```sh
gdb ./build-solution/assembly_parser
```

At the GDB prompt:

```text
set disassembly-flavor intel
tbreak *asm_parse_i64
run
x/s $rdi
set $saved_output = (long long *)$rsi
info registers rdi rsi rcx rax r8 r9 r10 r11
si
finish
print $eax
print *$saved_output
continue
```

The first readiness parse is `-1`; it returns success 1 and writes -1. Step through the sign, digit and bound checks before `finish` to record their state transitions. For an interactive boundary trace, set CLI arguments, then continue through the readiness calls to the requested operand. Addresses vary by run.

## Completion evidence

1. Complete only the named sign and bound tasks and pass both compilers in Debug and Release.
2. Record the three default rows and all three command results.
3. Trace the final digit of both signed limits and explain why the next out-of-range values fail.
4. Show a failed parse whose output canary is unchanged, plus invalid CLI input with exit 2 and no result.
5. Explain byte equality, pointer/index movement, unsigned magnitude checks and the defined sum arithmetic.

Independent study follows prediction, edit, test and trace. A guided session starts with the boundary table and a shared trace, followed by implementation and explanation of the first failed assertion. An optional extension can add a separately named base-specific parser with its own grammar and range tests after this contract passes.

## References

- [System V x86-64 ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [GNU assembler Intel syntax](https://sourceware.org/binutils/docs/as/i386_002dVariations.html)
- [GNU C integer conversion](https://sourceware.org/glibc/manual/latest/html_node/Parsing-of-Integers.html)
- [GDB instruction stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
